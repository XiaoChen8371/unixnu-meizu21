#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../firmware/Xnup.h"
static unsigned rng=0x865021;
static unsigned next(void) { rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5; return rng; }
static unsigned char *readall(const char *name, size_t *n) {
  FILE *f=fopen(name,"rb"); unsigned char *p;
  assert(f); assert(fseek(f,0,SEEK_END)==0); long len=ftell(f); assert(len>0);
  *n=(size_t)len; rewind(f); p=malloc(*n); assert(p);
  assert(fread(p,1,*n,f)==*n); fclose(f); return p;
}
int main(int argc,char **argv) {
  size_t n, sn; MZ_XNUP_VIEW v;
  assert(argc==3); unsigned char *b=readall(argv[1],&n), *small=readall(argv[2],&sn);
  assert(MzParseXnup(b,n,&v)); assert(v.KernelSize>1000000);
  assert(!MzParseXnup(b,n-1,&v));
  for (size_t i=0;i<sn;i++) assert(!MzParseXnup(small,i,&v));
  assert(MzParseXnup(small,sn,&v));
  unsigned char *mut=malloc(sn); assert(mut);
  for (unsigned i=0;i<100000;i++) {
    memcpy(mut,small,sn);
    for (unsigned j=0,count=1+next()%6;j<count;j++) mut[next()%sn]=(unsigned char)next();
    size_t cap=next()%(sn+1);
    if (MzParseXnup(mut,cap,&v)) {
      assert(v.TotalSize<=cap && v.Cmdline+v.CmdlineSize<=mut+cap);
      assert(v.Kernel>=mut && v.Kernel+v.KernelSize<=mut+cap);
    }
  }
  free(mut); free(small); free(b);
  puts("XNUP bounds: real payload, all fixture truncations, 100000 mutations PASS");
  return 0;
}
