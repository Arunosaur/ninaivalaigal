# Monthly SPEC Audit Automation Setup

**Last Updated**: November 1, 2025  
**Status**: Ready for Implementation

---

## Overview

Monthly SPEC audit automation can be set up in two ways:
1. **GitHub Actions** (Recommended) - Runs in CI/CD pipeline
2. **Cron Job** (Alternative) - Runs on local/server machine

---

## Option 1: GitHub Actions (Recommended)

### Setup Complete ✅

The GitHub Actions workflow is already created at:
`.github/workflows/monthly-spec-audit.yml`

### Features

- **Automatic Execution**: Runs on 1st of each month at 9:00 AM UTC
- **Manual Trigger**: Can be run manually via GitHub Actions UI
- **Artifact Storage**: Reports saved as artifacts (90 days audit, 365 days monthly)
- **Auto-Commit**: Reports automatically committed to repository
- **Health Score Checks**: Warns if health score drops below 70

### Schedule

- **Frequency**: Monthly on the 1st
- **Time**: 9:00 AM UTC
- **Cron**: `0 9 1 * *`
- **First Run**: December 1, 2025

### Manual Execution

To run manually:
1. Go to GitHub Actions tab
2. Select "Monthly SPEC Audit" workflow
3. Click "Run workflow"
4. Optionally specify a month (YYYY-MM format)

### Output

- **Audit Report**: `governance/reports/SPEC_INDEX_AUDIT_YYYY-MM-DD.md`
- **Monthly Report**: `governance/reports/SPEC_STATUS_MONTHLY_YYYY-MM.md`
- **Artifacts**: Available in GitHub Actions run artifacts
- **Summary**: Posted in workflow summary

### Verification

To verify setup:
1. Go to repository → Actions tab
2. Check "Monthly SPEC Audit" workflow exists
3. Click "Run workflow" to test
4. Verify reports are generated

---

## Option 2: Cron Job (Alternative)

### Setup Instructions

#### Step 1: Create Cron Entry

Edit crontab:
```bash
crontab -e
```

Add this line:
```cron
0 9 1 * * cd /Users/swami/WorkSpace/ninaivalaigal && /path/to/scripts/monthly_spec_audit.sh >> /tmp/spec_audit.log 2>&1
```

**Adjustments**:
- Change `/Users/swami/WorkSpace/ninaivalaigal` to your project path
- Ensure `monthly_spec_audit.sh` is executable: `chmod +x scripts/monthly_spec_audit.sh`

#### Step 2: Verify Cron

Test the cron entry:
```bash
# List current crontab
crontab -l

# Test script manually
cd /Users/swami/WorkSpace/ninaivalaigal
./scripts/monthly_spec_audit.sh
```

#### Step 3: Monitor Logs

Check execution logs:
```bash
tail -f /tmp/spec_audit.log
```

### Cron Schedule Options

**Monthly on 1st at 9 AM**:
```cron
0 9 1 * * /path/to/script
```

**Monthly on 1st at 9 AM (with conda)**:
```cron
0 9 1 * * source /path/to/conda/etc/profile.d/conda.sh && conda activate nina && cd /path/to/project && ./scripts/monthly_spec_audit.sh
```

**Weekly (for testing)**:
```cron
0 9 * * 1 /path/to/script  # Every Monday at 9 AM
```

---

## Verification Checklist

### GitHub Actions Setup ✅
- [x] Workflow file created: `.github/workflows/monthly-spec-audit.yml`
- [x] Schedule configured: `0 9 1 * *` (1st of month)
- [x] Manual trigger enabled
- [ ] First run scheduled: December 1, 2025
- [ ] Test run completed successfully

### Scripts Ready ✅
- [x] `scripts/monthly_spec_audit.sh` created and executable
- [x] `scripts/generate_monthly_spec_report.py` created
- [x] `scripts/audit_spec_index.py` enhanced
- [x] All scripts tested manually

### Reports Generated ✅
- [x] First monthly report: November 2025
- [x] Report format validated
- [x] Health score calculation verified

---

## First Automated Run

### Expected Date: December 1, 2025

### What Will Happen

1. **GitHub Actions** (if enabled):
   - Workflow triggers automatically at 9:00 AM UTC
   - Runs audit script
   - Generates December 2025 report
   - Commits reports to repository
   - Uploads artifacts
   - Posts summary

2. **Cron Job** (if enabled):
   - Script executes at scheduled time
   - Runs audit and generates report
   - Saves reports to `governance/reports/`
   - Logs output to `/tmp/spec_audit.log`

### Verification After First Run

Check:
- [ ] Audit report generated: `SPEC_INDEX_AUDIT_2025-12-01.md`
- [ ] Monthly report generated: `SPEC_STATUS_MONTHLY_2025-12.md`
- [ ] Reports committed to repository
- [ ] Health score calculated
- [ ] No errors in execution logs

---

## Troubleshooting

### GitHub Actions Issues

**Workflow not running**:
- Check workflow file syntax
- Verify cron schedule is correct
- Check GitHub Actions is enabled for repository

**Scripts fail**:
- Verify Python version (3.11+)
- Check script paths are correct
- Review workflow logs for errors

**Reports not committed**:
- Check repository permissions
- Verify git config in workflow
- Check if reports actually changed

### Cron Job Issues

**Script not executing**:
- Check cron daemon is running: `sudo systemctl status cron`
- Verify cron entry syntax: `crontab -l`
- Check script permissions: `chmod +x scripts/monthly_spec_audit.sh`
- Verify paths are absolute in cron entry

**Script fails silently**:
- Check log file: `tail -f /tmp/spec_audit.log`
- Verify conda environment path
- Check Python executable path

**Permission errors**:
- Ensure user has write access to `governance/reports/`
- Check git repository permissions
- Verify script is executable

---

## Maintenance

### Monthly Review

After each automated run:
1. Review generated reports
2. Check health score trends
3. Verify recommendations are actionable
4. Update automation if needed

### Quarterly Review

Every quarter:
1. Review automation effectiveness
2. Update health score targets
3. Refine report templates
4. Check for automation improvements

---

## Next Steps

### Immediate
1. ✅ **COMPLETE**: GitHub Actions workflow created
2. ⏳ **PENDING**: Enable workflow in repository (if not auto-enabled)
3. ⏳ **PENDING**: Test workflow manually to verify setup
4. ⏳ **PENDING**: Wait for December 1, 2025 first automated run

### Future Enhancements
- Add Slack/email notifications
- Create trend visualization
- Add health score alerting
- Integrate with project dashboard

---

**Status**: ✅ **AUTOMATION SETUP COMPLETE**

*Ready for first automated run on December 1, 2025*

