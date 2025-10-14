# Troubleshooting the SPEC Dashboard

## Common Issues and Solutions

### Issue: Dashboard is not updating after I changed a SPEC.

- **Solution:** Run the `spec-dashboard-generator.py` script to regenerate the dashboard data. The dashboard reads from a static JSON file, so it needs to be updated whenever the SPECs change.

### Issue: A SPEC is not appearing on the dashboard.

- **Solution:** Make sure the SPEC has a valid YAML front-matter block at the top of the `README.md` file. The dashboard generator will skip any SPECs with invalid or missing front-matter.

### Issue: The dashboard is showing old or incorrect data.

- **Solution:** Clear your browser cache and do a hard refresh. If the issue persists, run the `spec-dashboard-generator.py` script again to ensure the data is up-to-date.
