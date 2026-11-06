# UniXNU on Meizu 21 (SM8650)

Unofficial device adaptation work for running **UniXNU** on the Meizu 21 / Snapdragon 8 Gen 3 (SM8650, ARM64, UFS).

This repository publishes the **normal r20 transition source snapshot**. GPU bring-up experiments are intentionally excluded.

## Current status

- UniXNU graphical menu is working.
- The verified r20 boot path reaches the iOS 16.5 / Darwin 22 desktop.
- Display geometry, UFS storage access, and Goodix touch are working.
- The phone is owner-verified with working desktop and normal touch input.
- GPU hardware acceleration is **not complete**. The current normal version should not be described as having working Metal acceleration.

## Boot path

    ABL
      -> existing clean shim
      -> exact DEBUG UEFI firmware
      -> MeizuBootBridge
      -> UniXNU menu
      -> UNIXNU_LOADER_PROTOCOL
      -> retained Darwin 22 loader and XNU
      -> iOS 16.5

This is a transition-stage port. UniXNU provides the menu and loader protocol, while the already verified Darwin 22 kernel and hardware paths are retained. It is not yet a complete native UniXNU hardware-driver replacement.

## Source snapshot

The r20 device adaptation source is stored in [r20-device-source.tar](r20-device-source.tar). It includes the board profile, bridge source, packaging checks, memory-map audit, kernel-source inventory, and device evidence.

The corresponding uncompiled upstream inputs are pinned in unixnu.lock inside the archive:

- UniXNU: 04573c510c5fd4892ca6948739389141cc9e05f5
- DarwinBoot: 3c75734014cdab0acd9541e88057b7606ee7ae08
- OnePlus Ace 5 reference: aaa100d19f6fb14e5897a7e496edf7838d4d4e9f

## What is not included

This repository does **not** contain or distribute:

- iOS root or system images
- the protected super partition
- vendor firmware blobs
- complete boot images
- Apple SDK files
- device credentials or personal data

Build assistants must provide permitted local inputs and SDKs. The successful boot image is evidence for this specific device state, not a redistributable iOS image.

## Safety boundaries

- The super partition contains the iOS root and cryptex and must not be overwritten.
- boot_a, boot_b, slot state, and partition tables must be treated as device-specific.
- Back up a known working boot image before testing.
- Every UEFI build used for diagnosis should use DEBUG configuration.
- Memory-map additions must not overlap.
- Do not publish vendor firmware or proprietary Apple files.

## References and credit

This work depends on and references projects including UniXNU, DarwinBoot, earlier hackintosh-on-ARM experiments, the OnePlus SM8650 graphics-kernel sources, and other open device-porting work. Refer to the evidence and source manifests in the r20 snapshot for exact commits and file-level provenance. Upstream copyrights and licenses apply to their respective files.

## License

The repository contains material adapted from multiple upstream projects with different licenses. A repository-wide license has not been selected yet. Preserve the licenses and notices shipped with each source file or snapshot.
