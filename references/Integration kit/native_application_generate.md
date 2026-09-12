# Native DDS application generation

This guide generates the Connext Micro 4.3.0 C application for
`GCS_LEFT_2_Domain_6_Deployment` from `pdio_fl_system.xml` on Windows x64.

> Native deployment-aware generation is experimental in Connext Micro 4.3.0.
> This workflow supports C, not C++.

## 1. Set the environment

Open Command Prompt (`cmd.exe`) in this directory and set the installed Micro
location and target:

```batch
set "RTIMEHOME=C:\Program Files\rti_connext_dds-7.3.1\rti_connext_dds_micro-4.3.0_ER738"
set "RTIME_TARGET_NAME=x86_64lePEvs2017-Win10"
set "WORKSPACE=%CD%"
```

The schema path in `pdio_fl_system.xml` must resolve to:

```text
%RTIMEHOME%\rtiddsmag\resource\schema\dds-xml_system_definitions.xsd
```

## 2. Review the network configuration

Before running the application, update the values marked `[UPDATE REQUIRED]` in
the `GCS_LEFT_2_PDIO_FL_QosProfile` profile. In particular:

- `initial_peers` must contain reachable peer or multicast addresses.
- `interface_table/address` must be this host's IPv4 address, not a subnet address.
- `interface_table/net_mask` must match that interface.
- `allow_interfaces_list` must match `interface_table/interface_name`.

List the host's IPv4 addresses with:

```batch
ipconfig
```

The configured address must exist on the target host. An unassigned address causes
UDP multicast initialization to fail during `DDS_Init()`.

## 3. Generate the deployment application

MAG requires the output directory to exist:

```batch
if not exist native_output mkdir native_output

call "%RTIMEHOME%\rtiddsmag\scripts\rtiddsmag.bat" ^
    -language C ^
    pdio_fl_system.xml ^
    -d native_output ^
    -replace ^
    -deployment GCS_LEFT_2_Domain_6_Deployment ^
    -applicationType micro4 ^
    -verbosity 3
```

The application is generated under:

```text
native_output\MyDeploymentLib\MyDeploymentScenario\
GCS_LEFT_2_Domain_6_Deployment\GCS_LEFT_2_Domain_6_Application
```

## 4. Generate type support

MAG generates entity configuration but ignores the XML `<types>` section.
Run `rtiddsgen` from the `rtiddsmag` directory and place its output beside the
MAG-generated sources:

```batch
set "INPUT_XML=%WORKSPACE%\pdio_fl_system.xml"
set "APP_DIR=%WORKSPACE%\native_output\MyDeploymentLib\MyDeploymentScenario\GCS_LEFT_2_Domain_6_Deployment\GCS_LEFT_2_Domain_6_Application"

pushd "%RTIMEHOME%\rtiddsmag"
call "%RTIMEHOME%\rtiddsgen\scripts\rtiddsgen.bat" ^
    -create typefiles ^
    -micro ^
    -language C ^
    "%INPUT_XML%" ^
    -d "%APP_DIR%" ^
    -replace
popd
```

## 5. Build

Use a short build directory to avoid the Windows 260-character path limit:

```batch
set "BUILD_DIR=%WORKSPACE%\native_build"
cmake -S "%APP_DIR%" -B "%BUILD_DIR%" -DCMAKE_BUILD_TYPE=Release
cmake --build "%BUILD_DIR%" --config Release --parallel
```

The executable is written to:

```text
native_output\MyDeploymentLib\MyDeploymentScenario\
GCS_LEFT_2_Domain_6_Deployment\GCS_LEFT_2_Domain_6_Application\
objs\x86_64lePEvs2017-Win10\Release\GCS_LEFT_2_Domain_6_Application.exe
```

## 6. Run

After configuring an IPv4 interface that exists on the host:

```batch
"%APP_DIR%\objs\%RTIME_TARGET_NAME%\Release\GCS_LEFT_2_Domain_6_Application.exe"
```

The generated `DDS_Run()` loop does not return. Stop it with `Ctrl+C`.

Regenerate and rebuild after every change to `pdio_fl_system.xml`; generated
source files are overwritten by `-replace` and should not be edited directly.