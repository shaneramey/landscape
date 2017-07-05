def set_gce_credentials(gce_project, gce_region):
    # to load credentials:
    os.environ['GOOGLE_PROJECT'] = gce_project
    os.environ['GOOGLE_REGION'] = gce_region
    os.environ['GOOGLE_CREDENTIALS'] = vault_load_gce_creds()

