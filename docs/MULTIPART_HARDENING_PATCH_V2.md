# Multipart Hardening Patch v2

Adds:
- Executable magics for Mach-O and Java class.
- MP4/ISO-BMFF detection via 'ftyp' within first 12 bytes.
- Archive blocking on text endpoints (ZIP/7z/RAR/GZIP).
- UTF-8-only text policy helper (explicit rejections).
- Content-Transfer-Encoding guard (reject base64/quoted-printable for text).
- Stream-time per-part limiter scaffold for early abort.

See tests in tests/test_multipart_hardening_patch_v2.py.
