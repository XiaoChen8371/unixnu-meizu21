/* Pure bounded XNUP parser shared by firmware and host mutation checks. */
#ifndef MEIZU_XNUP_H
#define MEIZU_XNUP_H
#ifdef MZ_EDK2
typedef UINT8 MZ_U8;
typedef UINT32 MZ_U32;
typedef UINTN MZ_SIZE;
#else
#include <stdint.h>
#include <stddef.h>
typedef uint8_t MZ_U8;
typedef uint32_t MZ_U32;
typedef size_t MZ_SIZE;
#endif
typedef struct {
  const MZ_U8 *Kernel, *Ramdisk, *Cmdline, *Menu, *Loader;
  MZ_SIZE KernelSize, RamdiskSize, CmdlineSize, MenuSize, LoaderSize, TotalSize;
} MZ_XNUP_VIEW;
static MZ_U32 MzU32(const MZ_U8 *p) {
  return (MZ_U32)p[0] | (MZ_U32)p[1]<<8 | (MZ_U32)p[2]<<16 | (MZ_U32)p[3]<<24;
}
static int MzName(const MZ_U8 *p, const char *s) {
  MZ_SIZE n = 0;
  while (n < 16 && s[n] && p[n] == (MZ_U8)s[n]) n++;
  return n < 16 && s[n] == 0 && p[n] == 0;
}
static int MzHasZero(const MZ_U8 *p, MZ_SIZE n) {
  MZ_SIZE i;
  for (i=0; i<n; i++) if (p[i] == 0) return 1;
  return 0;
}
static int MzParseXnup(const MZ_U8 *data, MZ_SIZE capacity, MZ_XNUP_VIEW *out) {
  MZ_SIZE end, pos;
  MZ_XNUP_VIEW v = {0};
  if (!data || !out || capacity < 8 || MzU32(data) != 0x50554e58) return 0;
  end = MzU32(data+4);
  if (end > capacity-8) return 0;
  end += 8; pos = 8; v.TotalSize = end;
  while (pos <= end && end-pos >= 24) {
    const MZ_U8 *name = data+pos;
    MZ_SIZE n = MzU32(name+16), aligned;
    pos += 24;
    if (name[0] == 0) {
      if (pos != end || !v.Kernel || !v.Ramdisk || !v.Cmdline || v.KernelSize < 64 ||
          MzU32(v.Kernel) != 0xfeedfacf || v.CmdlineSize < 2 ||
          v.Cmdline[v.CmdlineSize-1] != 0 || MzHasZero(v.Cmdline,v.CmdlineSize-1)) return 0;
      if ((v.Menu != 0) != (v.Loader != 0)) return 0;
      *out = v; return 1;
    }
    if (n > end-pos || n > (MZ_SIZE)-1-15) return 0;
    aligned = (n+15) & ~(MZ_SIZE)15;
    if (aligned > end-pos || MzU32(name+20) != 0 || !MzHasZero(name,16)) return 0;
    if (MzName(name,"kernel")) {
      if (v.Kernel) return 0;
      v.Kernel = data+pos; v.KernelSize = n;
    } else if (MzName(name,"ramdisk")) {
      if (v.Ramdisk) return 0;
      v.Ramdisk = data+pos; v.RamdiskSize = n;
    } else if (MzName(name,"cmdline")) {
      if (v.Cmdline) return 0;
      v.Cmdline = data+pos; v.CmdlineSize = n;
    } else if (MzName(name,"unixnu")) {
      if (v.Menu || n < 128 || data[pos] != 'M' || data[pos+1] != 'Z') return 0;
      v.Menu = data+pos; v.MenuSize = n;
    } else if (MzName(name,"loader")) {
      if (v.Loader || n < 128 || data[pos] != 'M' || data[pos+1] != 'Z') return 0;
      v.Loader = data+pos; v.LoaderSize = n;
    } else return 0; // No USB, alternate physical window or checkpoint entries.
    pos += aligned;
  }
  return 0;
}
#endif
