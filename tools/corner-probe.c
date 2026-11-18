#include <ApplicationServices/ApplicationServices.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

extern int SLSMainConnectionID(void);
extern CFTypeRef SLSWindowQueryWindows(int cid, CFArrayRef windows, uint32_t options);
extern CFTypeRef SLSWindowQueryResultCopyWindows(CFTypeRef query);
extern bool SLSWindowIteratorAdvance(CFTypeRef iterator);
extern uint32_t SLSWindowIteratorGetWindowID(CFTypeRef iterator);

typedef CFArrayRef (*GetCornerRadii)(CFTypeRef iterator);

static int radius_of(int cid, GetCornerRadii get_radii, uint32_t wid, double *out) {
  CFNumberRef number = CFNumberCreate(NULL, kCFNumberSInt32Type, &wid);
  CFArrayRef target = CFArrayCreate(NULL, (const void **)&number, 1, &kCFTypeArrayCallBacks);
  CFRelease(number);
  int found = 0;
  CFTypeRef query = SLSWindowQueryWindows(cid, target, 0);
  if (query) {
    CFTypeRef iterator = SLSWindowQueryResultCopyWindows(query);
    if (iterator && SLSWindowIteratorAdvance(iterator) && SLSWindowIteratorGetWindowID(iterator) == wid) {
      CFArrayRef radii = get_radii(iterator);
      if (radii && CFArrayGetCount(radii) > 0) {
        found = CFNumberGetValue(CFArrayGetValueAtIndex(radii, 0), kCFNumberDoubleType, out);
      }
      if (radii) CFRelease(radii);
    }
    if (iterator) CFRelease(iterator);
    CFRelease(query);
  }
  CFRelease(target);
  return found;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: corner-probe <owner-name>\n");
    return 2;
  }
  void *skylight = dlopen("/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight", RTLD_LAZY | RTLD_LOCAL);
  GetCornerRadii get_radii = skylight ? (GetCornerRadii)dlsym(skylight, "SLSWindowIteratorGetCornerRadii") : NULL;
  if (!get_radii) {
    fprintf(stderr, "SLSWindowIteratorGetCornerRadii unavailable\n");
    return 3;
  }
  int cid = SLSMainConnectionID();
  CFArrayRef windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements, kCGNullWindowID);
  CFStringRef wanted = CFStringCreateWithCString(NULL, argv[1], kCFStringEncodingUTF8);
  int matched = 0;
  for (CFIndex i = 0; i < CFArrayGetCount(windows); i++) {
    CFDictionaryRef info = CFArrayGetValueAtIndex(windows, i);
    CFStringRef owner = CFDictionaryGetValue(info, kCGWindowOwnerName);
    CFNumberRef layer = CFDictionaryGetValue(info, kCGWindowLayer);
    int layer_value = -1;
    if (layer) CFNumberGetValue(layer, kCFNumberIntType, &layer_value);
    if (!owner || CFStringCompare(owner, wanted, 0) != kCFCompareEqualTo || layer_value != 0) continue;
    uint32_t wid = 0;
    CFNumberGetValue(CFDictionaryGetValue(info, kCGWindowNumber), kCFNumberSInt32Type, &wid);
    CGRect bounds = CGRectZero;
    CGRectMakeWithDictionaryRepresentation(CFDictionaryGetValue(info, kCGWindowBounds), &bounds);
    double radius = 0;
    if (radius_of(cid, get_radii, wid, &radius)) {
      printf("wid=%u size=%.0fx%.0f radius=%.2f\n", wid, bounds.size.width, bounds.size.height, radius);
    } else {
      printf("wid=%u size=%.0fx%.0f radius=unknown\n", wid, bounds.size.width, bounds.size.height);
    }
    matched++;
  }
  CFRelease(wanted);
  CFRelease(windows);
  if (matched == 0) {
    fprintf(stderr, "no on-screen windows owned by %s\n", argv[1]);
    return 1;
  }
  return 0;
}
