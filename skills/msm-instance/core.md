# msm-instance Legacy Core

`msm-instance` is a compatibility shim.
The implementation and documentation moved to `../msm-record-archive/`.

Use:

```bash
scripts/msm-record-archive init --target REPO --apply
scripts/msm-record-archive insert --target REPO --table TABLE --data JSON --apply
scripts/msm-record-archive export-snapshot --target REPO --apply
```
