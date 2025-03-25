# OCI Setup Guide

This guide explains how to set up Oracle Cloud Infrastructure (OCI) credentials for use with the MCP Server.

## Prerequisites

- Oracle Cloud Infrastructure account
- OCI CLI (optional, but recommended for testing)

## Setting Up OCI Credentials

### Option 1: Using an OCI Configuration File (Recommended)

1. **Create an API Key**

   a. Log in to the OCI Console.
   
   b. Click on your profile icon in the top-right corner and select "User Settings".
   
   c. Under "Resources", click on "API Keys".
   
   d. Click "Add API Key".
   
   e. Select "Generate API Key Pair" and download both the private and public keys.
   
   f. Click "Add" to add the key to your user.
   
   g. After adding the key, you'll see a configuration file snippet. Save this information.

2. **Create the OCI Configuration File**

   a. Create a directory for OCI configuration:
   
   ```bash
   mkdir -p ~/.oci
   ```
   
   b. Create a configuration file:
   
   ```bash
   touch ~/.oci/config
   chmod 600 ~/.oci/config
   ```
   
   c. Copy the configuration file snippet from the OCI Console into this file:
   
   ```
   [DEFAULT]
   user=ocid1.user.oc1..aaaaaaaa...
   fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
   tenancy=ocid1.tenancy.oc1..aaaaaaaa...
   region=us-ashburn-1
   key_file=~/.oci/oci_api_key.pem
   ```
   
   d. Move your private key to the specified location:
   
   ```bash
   mv /path/to/downloaded/private_key.pem ~/.oci/oci_api_key.pem
   chmod 600 ~/.oci/oci_api_key.pem
   ```

3. **Update the MCP Server Configuration**

   In your `config.yaml` file, set the following:
   
   ```yaml
   oci:
     config_file_path: "~/.oci/config"
     profile_name: "DEFAULT"
   ```

### Option 2: Direct Configuration

If you prefer not to use a configuration file, you can provide the credentials directly in the MCP Server configuration:

1. **Create an API Key** (follow steps 1a-1f from Option 1)

2. **Update the MCP Server Configuration**

   In your `config.yaml` file, set the following:
   
   ```yaml
   oci:
     user_ocid: "ocid1.user.oc1..example"
     fingerprint: "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
     tenancy_ocid: "ocid1.tenancy.oc1..example"
     region: "us-ashburn-1"
     key_file_path: "~/.oci/oci_api_key.pem"
   ```

## Verifying the Configuration

To verify that your OCI credentials are working correctly:

1. **Install the OCI CLI** (if not already installed):

   ```bash
   pip install oci-cli
   ```

2. **Test the configuration**:

   ```bash
   oci iam region list
   ```

   If configured correctly, this should return a list of available regions.

## Setting Up Required IAM Policies

For the MCP Server to provision resources, you need to ensure that your user has the appropriate permissions. Here's a basic policy that grants the necessary permissions:

```
Allow group <your-group> to manage all-resources in tenancy
```

For a more restrictive approach, you can limit the permissions to specific resource types:

```
Allow group <your-group> to manage compute-family in tenancy
Allow group <your-group> to manage virtual-network-family in tenancy
Allow group <your-group> to manage database-family in tenancy
Allow group <your-group> to manage object-family in tenancy
Allow group <your-group> to manage load-balancers in tenancy
```

## Troubleshooting

### Common Issues

1. **"Authorization failed or requested resource not found"**
   - Verify that your API key is correctly configured
   - Check that the fingerprint matches the one in the OCI Console
   - Ensure the private key file is in the correct location and has the right permissions

2. **"Not authorized to perform this request"**
   - Check that your user has the necessary IAM policies assigned

3. **"Region not found"**
   - Verify that the region specified in your configuration is valid

### Logging

The MCP Server logs OCI client operations. Check the logs for detailed error messages:

```bash
tail -f logs/mcp_server.log
```
