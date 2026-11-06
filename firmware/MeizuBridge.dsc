[Defines]
  PLATFORM_NAME = MeizuBridge
  PLATFORM_GUID = A183E2C0-4AE6-4D52-84F7-566D2EF1D5AD
  PLATFORM_VERSION = 0.1
  DSC_SPECIFICATION = 0x0001001C
!ifdef MEIZU_QEMU_TEST
  OUTPUT_DIRECTORY = Build/MeizuBridgeQemu
!else
  OUTPUT_DIRECTORY = Build/MeizuBridge
!endif
  SUPPORTED_ARCHITECTURES = AARCH64
  BUILD_TARGETS = DEBUG
  SKUID_IDENTIFIER = DEFAULT
!include MdePkg/MdeLibs.dsc.inc
[LibraryClasses]
  BaseLib|MdePkg/Library/BaseLib/BaseLib.inf
  BaseMemoryLib|MdePkg/Library/BaseMemoryLib/BaseMemoryLib.inf
  DevicePathLib|MdePkg/Library/UefiDevicePathLib/UefiDevicePathLib.inf
  MemoryAllocationLib|MdePkg/Library/UefiMemoryAllocationLib/UefiMemoryAllocationLib.inf
  PcdLib|MdePkg/Library/BasePcdLibNull/BasePcdLibNull.inf
  PrintLib|MdePkg/Library/BasePrintLib/BasePrintLib.inf
  UefiApplicationEntryPoint|MdePkg/Library/UefiApplicationEntryPoint/UefiApplicationEntryPoint.inf
  UefiBootServicesTableLib|MdePkg/Library/UefiBootServicesTableLib/UefiBootServicesTableLib.inf
  UefiRuntimeServicesTableLib|MdePkg/Library/UefiRuntimeServicesTableLib/UefiRuntimeServicesTableLib.inf
  UefiLib|MdePkg/Library/UefiLib/UefiLib.inf
  DebugLib|MdePkg/Library/UefiDebugLibStdErr/UefiDebugLibStdErr.inf
  DebugPrintErrorLevelLib|MdePkg/Library/BaseDebugPrintErrorLevelLib/BaseDebugPrintErrorLevelLib.inf
[PcdsFixedAtBuild]
  gEfiMdePkgTokenSpaceGuid.PcdDebugPrintErrorLevel|0x80000000
  gEfiMdePkgTokenSpaceGuid.PcdDebugPropertyMask|0x07
[Components]
  firmware/MeizuBootBridge.inf
!ifdef MEIZU_QEMU_TEST
[BuildOptions]
  *_CLANGPDB_AARCH64_CC_FLAGS = -DMEIZU_QEMU_TEST=1
!endif
