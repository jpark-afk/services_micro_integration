# Customer Preparation Steps

This guide describes the customer-side steps required before generating the AUTOSAR DdsCdd and the native TestApp.

Run all commands from the project folder, for example:

```bat
cd projects\projectName
```

## 1. Prepare the XML File

Run the XML patch script once:

```bat
.\user_work\patch_run.bat
```

The script processes the original XML file and automatically fills in required elements such as deployment-related information. It writes a patched system XML file under `user_work\`, for example `wpc_system.xml` or another `xxx_system.xml` file depending on the project configuration.

After the patched XML is generated, open it and search for the keyword `REQUIRED`.

Each `REQUIRED` placeholder must be replaced with the value that matches the customer's target system.

## 2. Generate DdsCdd

Open `generate_ddscdd.bat` and update the following variables for the customer's local RTI installation:

```bat
set "RTIMEHOME=<path-to-rti-connext-micro>"
set "JRE_HOME=<path-to-rti-jre>"
```

Make sure the XML path and deployment name in the script point to the patched XML and the deployment that should be used for AUTOSAR CDD generation.

Then run:

```bat
.\generate_ddscdd.bat
```

## 3. Generate the Native TestApp

Copy the patched system XML to a separate TestApp XML file:

```bat
copy /Y ".\user_work\<xxx_system.xml>" ".\user_work\test_system.xml"
```

Open `user_work\test_system.xml` and configure the `transport_builtin` value for the participant that will be simulated on the PC.

In most cases, replace the `10BASE-T1S` interface name with the actual network interface name used by the PC. There are usually two `transport_builtin` locations to update.

Use the following command to check the available Windows network interface names:

```bat
ipconfig /all
```

Open `generate_testapp_native.bat` and update the following variables for the customer's local RTI installation:

```bat
set "RTIMEHOME=<path-to-rti-connext-micro>"
set "JRE_HOME=<path-to-rti-jre>"
```

Set `MAG_DEPLOYMENT` to the deployment name of the participant that will be simulated by the native TestApp. The deployment name must exist in `user_work\test_system.xml`.

Example:

```bat
set "MAG_DEPLOYMENT=GCS_RIGHT_1_Domain_1_Deployment"
```

Then run:

```bat
.\generate_testapp_native.bat
```

The generated TestApp files are written under the `testapp\` folder.

## 4. Build the Native TestApp

If `generate_testapp_native.bat` completes successfully, a `testapp\` folder is created under the project folder.

Open `build_testapp_native.bat` and update the following variables for the customer's local RTI installation:

```bat
set "RTIMEHOME=<path-to-rti-connext-micro>"
set "JRE_HOME=<path-to-rti-jre>"
```

Check that `TARGET_NAME` matches the customer's target platform.

For a typical Windows setup using Visual Studio 2017, the target is usually:

```bat
set "TARGET_NAME=x86_64lePEvs2017-Win10"
```

Then run:

```bat
.\build_testapp_native.bat
```

The build output is written under `testapp\objs\`.

## Prerequisite: Install the Micro 4.3 Development PIL

Before building the native TestApp, download the RTI Connext Micro 4.3 development PIL package for the customer host environment.

1. Go to [RTI Downloads](https://support.rti.com/s/downloads).
2. Select `RTI Connext Micro Product`.
3. Select the required `4.x.x` version.
4. Select the host OS, either Windows or Linux, depending on the customer environment.
5. Download the target package, for example:

```text
rti_connext_dds_micro-4.x.x-target-<architecture>.rtipkg
```

Install the downloaded package by using Connext Professional Launcher or Connext Drive Launcher.

The package is typically installed under a path similar to:

```text
rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0\lib
```

Copy the installed PIL files into the actual Connext Micro folder used by this project. For example:

```text
rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738
```

This step collects the required Windows or Linux development PIL files into the Micro installation that is referenced by the project scripts.
