/** Meizu 21 Darwin 22 transition loader for the UniXNU loader protocol.
 * Board-specific, read-only payload filesystem. No block I/O or flash writes.
 * The existing XNUP/ADT handoff is retained until native DarwinBoot is ported.
 */
#include <Uefi.h>
#include <Library/BaseLib.h>
#include <Library/BaseMemoryLib.h>
#include <Library/MemoryAllocationLib.h>
#include <Library/UefiBootServicesTableLib.h>
#include <Library/UefiRuntimeServicesTableLib.h>
#include <Library/UefiLib.h>
#include <Library/DevicePathLib.h>
#include <Protocol/LoadedImage.h>
#include <Protocol/SimpleFileSystem.h>
#include <Protocol/GraphicsOutput.h>
#include <Protocol/UniXNULoader.h>
#include <Guid/FileInfo.h>
#include <Guid/FileSystemInfo.h>
#include "BridgeAssets.h"
#define MZ_EDK2 1
#include "Xnup.h"

typedef struct {
  EFI_FILE_PROTOCOL Protocol;
  CONST UINT8 *Data;
  UINTN Size;
  UINTN Position;
  BOOLEAN Directory;
} MEMORY_FILE;

STATIC EFI_HANDLE mVolume;
STATIC EFI_HANDLE mImage;
STATIC CONST UINT8 *mKernel;
STATIC UINTN mKernelSize;
STATIC CONST UINT8 *mMenu;
STATIC UINTN mMenuSize;
#ifndef MEIZU_QEMU_TEST
STATIC CONST UINT8 *mLegacy;
STATIC UINTN mLegacySize;
#endif
STATIC UINTN mFileReads;
STATIC EFI_FILE_PROTOCOL mFileTemplate;
STATIC EFI_GUID mVolumeGuid = {0x2b4cd977,0x14d7,0x482e,{0xbb,0xb8,0x88,0x98,0xe0,0x76,0xd1,0x91}};

STATIC EFI_STATUS EFIAPI CloseFile(EFI_FILE_PROTOCOL *This) {
  FreePool(This); return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI DeleteFile(EFI_FILE_PROTOCOL *This) {
  CloseFile(This); return EFI_WARN_DELETE_FAILURE;
}
STATIC EFI_STATUS EFIAPI ReadFile(EFI_FILE_PROTOCOL *This, UINTN *Size, VOID *Buffer) {
  MEMORY_FILE *File = (MEMORY_FILE *)This;
  if (Size == NULL || (*Size != 0 && Buffer == NULL)) return EFI_INVALID_PARAMETER;
  if (File->Directory) { *Size = 0; return EFI_SUCCESS; }
  *Size = MIN(*Size, File->Size - File->Position);
  if (*Size != 0) CopyMem(Buffer, File->Data + File->Position, *Size);
  File->Position += *Size; mFileReads++; return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI WriteFile(EFI_FILE_PROTOCOL *This, UINTN *Size, VOID *Buffer) {
  return EFI_WRITE_PROTECTED;
}
STATIC EFI_STATUS EFIAPI GetPosition(EFI_FILE_PROTOCOL *This, UINT64 *Position) {
  if (Position == NULL) return EFI_INVALID_PARAMETER;
  *Position = ((MEMORY_FILE *)This)->Position; return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI SetPosition(EFI_FILE_PROTOCOL *This, UINT64 Position) {
  MEMORY_FILE *File = (MEMORY_FILE *)This;
  if (Position == MAX_UINT64) Position = File->Size;
  if (Position > File->Size) return EFI_INVALID_PARAMETER;
  File->Position = (UINTN)Position; return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI GetInfo(EFI_FILE_PROTOCOL *This, EFI_GUID *Guid, UINTN *Size, VOID *Buffer) {
  MEMORY_FILE *File = (MEMORY_FILE *)This;
  UINTN Need;
  if (Guid == NULL || Size == NULL) return EFI_INVALID_PARAMETER;
  if (CompareGuid(Guid, &gEfiFileInfoGuid)) {
    EFI_FILE_INFO *Info;
    Need = SIZE_OF_EFI_FILE_INFO + sizeof(L"payload");
    if (*Size < Need) { *Size = Need; return EFI_BUFFER_TOO_SMALL; }
    if (Buffer == NULL) return EFI_INVALID_PARAMETER;
    ZeroMem(Buffer, Need); Info = Buffer;
    Info->Size = Need; Info->FileSize = File->Size; Info->PhysicalSize = File->Size;
    Info->Attribute = EFI_FILE_READ_ONLY | (File->Directory ? EFI_FILE_DIRECTORY : 0);
    CopyMem(Info->FileName, L"payload", sizeof(L"payload"));
  } else if (CompareGuid(Guid, &gEfiFileSystemInfoGuid)) {
    EFI_FILE_SYSTEM_INFO *Info;
    Need = SIZE_OF_EFI_FILE_SYSTEM_INFO + sizeof(L"MEIZU21");
    if (*Size < Need) { *Size = Need; return EFI_BUFFER_TOO_SMALL; }
    if (Buffer == NULL) return EFI_INVALID_PARAMETER;
    ZeroMem(Buffer, Need); Info = Buffer;
    Info->Size = Need; Info->ReadOnly = TRUE; Info->VolumeSize = mKernelSize;
    Info->BlockSize = 512; CopyMem(Info->VolumeLabel, L"MEIZU21", sizeof(L"MEIZU21"));
  } else return EFI_UNSUPPORTED;
  *Size = Need; return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI SetInfo(EFI_FILE_PROTOCOL *This, EFI_GUID *Guid, UINTN Size, VOID *Buffer) {
  return EFI_WRITE_PROTECTED;
}
STATIC EFI_STATUS EFIAPI FlushFile(EFI_FILE_PROTOCOL *This) { return EFI_SUCCESS; }

STATIC EFI_STATUS EFIAPI OpenFile(EFI_FILE_PROTOCOL *This, EFI_FILE_PROTOCOL **Out,
    CHAR16 *Name, UINT64 Mode, UINT64 Attributes) {
  MEMORY_FILE *File;
  CONST UINT8 *Data = NULL;
  UINTN Size = 0;
  BOOLEAN Directory = FALSE;
  if (Out == NULL || Name == NULL) return EFI_INVALID_PARAMETER;
  *Out = NULL;
  if (Mode != EFI_FILE_MODE_READ) return EFI_WRITE_PROTECTED;
  if (!((MEMORY_FILE *)This)->Directory) return EFI_NOT_FOUND;
  // This filesystem is an absolute-path payload provider, with a single root.
  while (*Name == L'\\') Name++;
  if (*Name == 0 || StrCmp(Name, L".") == 0) Directory = TRUE;
  else if (StrCmp(Name, L"EFI\\UniXNU\\unixnu.toml") == 0) {
    Data = gBootConfig; Size = gBootConfigSize;
  } else if (StrCmp(Name, L"EFI\\UniXNU\\Payloads\\kernel.macho") == 0) {
    Data = mKernel; Size = mKernelSize;
  } else return EFI_NOT_FOUND;
  File = AllocateZeroPool(sizeof(*File));
  if (File == NULL) return EFI_OUT_OF_RESOURCES;
  File->Protocol = mFileTemplate; File->Data = Data; File->Size = Size;
  File->Directory = Directory; *Out = &File->Protocol; return EFI_SUCCESS;
}
STATIC EFI_STATUS EFIAPI OpenVolume(EFI_SIMPLE_FILE_SYSTEM_PROTOCOL *This, EFI_FILE_PROTOCOL **Root) {
  MEMORY_FILE Parent;
  ZeroMem(&Parent, sizeof(Parent)); Parent.Directory = TRUE;
  return OpenFile(&Parent.Protocol, Root, L"\\", EFI_FILE_MODE_READ, 0);
}
STATIC EFI_SIMPLE_FILE_SYSTEM_PROTOCOL mFs = { EFI_SIMPLE_FILE_SYSTEM_PROTOCOL_REVISION, OpenVolume };
STATIC EFI_FILE_PROTOCOL mFileTemplate = {
  EFI_FILE_PROTOCOL_REVISION, OpenFile, CloseFile, DeleteFile, ReadFile, WriteFile,
  GetPosition, SetPosition, GetInfo, SetInfo, FlushFile, NULL, NULL, NULL, NULL
};

STATIC EFI_STATUS StartEmbedded(CONST UINT8 *Bytes, UINTN Size, CHAR16 *Path) {
  EFI_STATUS Status;
  EFI_HANDLE Child;
  EFI_LOADED_IMAGE_PROTOCOL *Loaded;
  EFI_DEVICE_PATH_PROTOCOL *DevicePath = FileDevicePath(mVolume, Path);
  if (DevicePath == NULL) return EFI_OUT_OF_RESOURCES;
  Status = gBS->LoadImage(FALSE, mImage, DevicePath, (VOID *)Bytes, Size, &Child);
  FreePool(DevicePath);
  if (EFI_ERROR(Status)) return Status;
  Status = gBS->HandleProtocol(Child, &gEfiLoadedImageProtocolGuid, (VOID **)&Loaded);
  if (!EFI_ERROR(Status)) { Loaded->DeviceHandle = mVolume; Status = gBS->StartImage(Child, NULL, NULL); }
  gBS->UnloadImage(Child);
  return Status;
}

STATIC EFI_STATUS EFIAPI BootCompat(UNIXNU_LOADER_PROTOCOL *This,
    CONST UNIXNU_LOADER_BOOT_REQUEST *Request) {
  EFI_FILE_PROTOCOL *Root = NULL, *File = NULL;
  EFI_STATUS Status;
  UINTN Size;
  UINT8 Check[64];
  if (Request == NULL || Request->Volume != mVolume || Request->KernelPath == NULL ||
      StrCmp(Request->KernelPath, L"\\EFI\\UniXNU\\Payloads\\kernel.macho") != 0 ||
      Request->BootArgs == NULL || StrCmp(Request->BootArgs, gExpectedArgs) != 0 ||
      Request->DeviceTree != NULL || Request->DeviceTreeSize != 0 ||
      Request->Ramdisk != NULL || Request->RamdiskSize != 0 || Request->KextCount != 0)
    return EFI_UNSUPPORTED;
  // Exercise the same immutable volume that UniXNU resolved. The legacy loader
  // consumes exactly this kernel, from the validated, retained XNUP in RAM.
  Status = mFs.OpenVolume(&mFs, &Root);
  if (!EFI_ERROR(Status)) Status = Root->Open(Root, &File, (CHAR16 *)Request->KernelPath, EFI_FILE_MODE_READ, 0);
  if (Root != NULL) Root->Close(Root);
  if (EFI_ERROR(Status)) return Status;
  Size = sizeof(Check); Status = File->Read(File, &Size, Check); File->Close(File);
  if (EFI_ERROR(Status) || Size != sizeof(Check) || CompareMem(Check, mKernel, Size) != 0)
    return EFI_COMPROMISED_DATA;
#ifdef MEIZU_QEMU_TEST
  Print(L"MEIZU-BRIDGE: protocol handoff PASS; immutable file reads %u\n", (UINT32)mFileReads);
  gRT->ResetSystem(EfiResetShutdown, EFI_SUCCESS, 0, NULL);
  return EFI_ABORTED;
#else
  return StartEmbedded(mLegacy, mLegacySize, L"\\EFI\\UniXNU\\LegacyLoader.efi");
#endif
}
STATIC UNIXNU_LOADER_PROTOCOL mLoader = { UNIXNU_LOADER_REVISION, BootCompat };

EFI_STATUS EFIAPI MeizuBootBridgeEntry(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable) {
  EFI_STATUS Status;
  VENDOR_DEVICE_PATH Vendor;
  EFI_DEVICE_PATH_PROTOCOL *DevicePath;
  mImage = ImageHandle;
#ifdef MEIZU_QEMU_TEST
  // Compile the parser in both variants; test data never points at phone MMIO.
  MZ_XNUP_VIEW View;
  if (!MzParseXnup(gTestPayload, gTestPayloadSize, &View)) return EFI_COMPROMISED_DATA;
  mKernel = View.Kernel; mKernelSize = View.KernelSize;
  mMenu = gUniXnuImage; mMenuSize = gUniXnuImageSize;
#else
  EFI_GRAPHICS_OUTPUT_PROTOCOL *Gop;
  MZ_XNUP_VIEW View;
  Status = gBS->LocateProtocol(&gEfiGraphicsOutputProtocolGuid, NULL, (VOID **)&Gop);
  if (EFI_ERROR(Status) || Gop->Mode == NULL || Gop->Mode->Info == NULL ||
      Gop->Mode->FrameBufferBase != 0xE3940000ULL) return EFI_UNSUPPORTED;
  if (!MzParseXnup((CONST UINT8 *)(UINTN)0xF0000000ULL, 0x3800000, &View) ||
      View.KernelSize != gExpectedKernelSize ||
      View.Menu == NULL || View.MenuSize != gExpectedMenuSize ||
      View.Loader == NULL || View.LoaderSize != gExpectedLoaderSize ||
      AsciiStrCmp((CONST CHAR8 *)View.Cmdline, gExpectedAsciiArgs) != 0)
    return EFI_COMPROMISED_DATA;
  mKernel = View.Kernel; mKernelSize = View.KernelSize;
  mMenu = View.Menu; mMenuSize = View.MenuSize;
  mLegacy = View.Loader; mLegacySize = View.LoaderSize;
  // r16's corrected visible panel geometry, without moving the framebuffer.
  Gop->Mode->Info->VerticalResolution = 2340;
  Gop->Mode->FrameBufferSize = 4320U * 2340U;
#endif
  ZeroMem(&Vendor, sizeof(Vendor));
  Vendor.Header.Type = HARDWARE_DEVICE_PATH; Vendor.Header.SubType = HW_VENDOR_DP;
  SetDevicePathNodeLength(&Vendor.Header, sizeof(Vendor)); Vendor.Guid = mVolumeGuid;
  DevicePath = AppendDevicePathNode(NULL, &Vendor.Header);
  if (DevicePath == NULL) return EFI_OUT_OF_RESOURCES;
  Status = gBS->InstallMultipleProtocolInterfaces(&mVolume,
      &gEfiDevicePathProtocolGuid, DevicePath, &gEfiSimpleFileSystemProtocolGuid, &mFs,
      &gUniXNULoaderProtocolGuid, &mLoader, NULL);
  if (EFI_ERROR(Status)) { FreePool(DevicePath); return Status; }
  Print(L"MEIZU-BRIDGE: read-only payload ready; Darwin22 compatibility\n");
  Status = StartEmbedded(mMenu, mMenuSize, L"\\EFI\\UniXNU\\UniXNU.efi");
  gBS->UninstallMultipleProtocolInterfaces(mVolume, &gEfiDevicePathProtocolGuid, DevicePath,
      &gEfiSimpleFileSystemProtocolGuid, &mFs, &gUniXNULoaderProtocolGuid, &mLoader, NULL);
  FreePool(DevicePath);
  return Status;
}
