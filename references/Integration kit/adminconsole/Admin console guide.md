# RTI Admin Console: A Step-by-Step Guide for Connext Micro Applications

This guide provides an overview of how to use the RTI Admin Console to monitor topics, subscribe to data, and publish data within a remote Connext Micro application.

**Note: This guide explains how to validate an example application using a simple DDS-XML.  To use a production DDS-XML, refer to the section in the [annex](#annex) on configuring Admin Console QoS.**

# Prerequisites

RTI Admin Console is part of the tools included with RTI Connext Drive. Please make sure this is installed before following this guide.

Also, the Graphical Data Publishing feature uses Connext Python API to populate the data. Make sure there is a Python interpreter installed. Do not use the Windows Store interpreter. Check this [Knowledge Base Article](https://community.rti.com/kb/admin-console-fails-load-python-configuration) in case you run into problems regarding Python.

# 1\. Discovering a Connext Micro Application

## 1.1 Launching Admin Console

Execute the RTI Launcher from your Connext installation.

You can find Admin Console within the “Tools” tab.
![][image1]
The first time you run Admin Console, the following prompt will show.
Choose the option “Manually join and leave domains”.

If this message doesn’t appear, that’s OK. We'll apply the right configuration in the following sections.
![][image2]

## 1.2 Discovering Your Application

The following steps explain how to configure Admin Console to discover the Connext Micro application.

**Note**: if the Micro application uses multicast, only the Domain configuration in the below is needed.

### 1.2.1 Configure custom Initial Peers

1. Go to View \> Preferences.
   ![][image3]

2. In the Preferences dialog, select the Administration tab.

3. Select “Manually join and leave domains”. Specify the domain of your application. Then click “Join Domains”
   ![][image4]

4. **(Only if you are not using multicast)**, click the domains and then "Edit DomainParticipant(s)" to open the Edit DomainParticipant settings dialog.
   ![][image5]

5. **(Only if you are not using multicast)** Add the IP address of the Micro application that you want to connect in this dialog.
   ![][image6]
   After adding the peer address:
   ![][image7]

## 1.3 Navigating the DDS Logical View

1. Once a domain is joined, the "DDS Logical View" will display a list of discovered Topics

2. Expand the "Domain" nodes to see all active topics in the domain.
   ![][image8]

3. Click on a topic to see the associated DataWriters and DataReaders in the main pane.
   ![][image9]

# 2\. Subscribing to Data Using Admin Console

Admin Console enables you to dynamically subscribe to topics and view the data being published by your Connext Micro application.

## 2.1 Initiating a Subscription

1. In the "DDS Logical View," right-click on the desired topic.
2. Select "Subscribe".
   ![][image10]
3. A new window will let you configure the subscriber options. Since Micro doesn’t propagate the Type definitions, you need to load them from the DDS-XML file corresponding to the Micro application currently in use. Select “Load Data Types from XML file”, click the “+” symbol, and select the XML file that contains the datatypes.
   ![][image11]![][image12]
4. After adding the file, **uncheck “Hide irrelevant types”** and you should be able to find the type in the dropdown menu. Click “OK” to start subscribing to data.
   **![][image13]**

## 2.2 Confirming reception of data (Validating Data Published by the MCU)

1. Admin Console will ask you to switch to the “Visualization Perspective”, click yes. (If you later want to go back to the “Administration Perspective”, click Administration button ![][image14] on the top-right corner)
   ![][image15]

2. Select the “Topic Data” tab in the Topic view. You will find a table with the last value of each instance.
   ![][image16]

3. To confirm that samples are being constantly published, right click on the topic from the “DDS Logical View” and select “Visualize”\>”Sample Log”
   ![][image17]

4. The Sample Log shows each sample received since it was opened, **if you see samples being added, the Micro application is currently publishing, therefore validation is OK.**
   ![][image18]
   You can click any of them to get its content and metadata

# 3\. Publishing Data Using Admin Console

The Admin Console can also be used to publish data to topics, which is useful for validating data reception in your Connext Micro application.

## 3.1 Creating a Publisher

1. In the "DDS Logical View," right-click on the desired topic.
2. Select "Publish".
   ![][image19]
3. A new window will let you configure the publisher options similar to the one for subscribing. Since Micro doesn’t propagate the Type definitions, you need to load them from the DDS-XML file corresponding to the Micro application currently in use. Select “Load Data Types from XML file”, click the “+” symbol, and select the XML file that contains the datatypes. Set the correct Data Type for the topic.
   ![][image20]

## 3.2 Publishing

1. In the "Publication" tab of the topic, you will see a template for the topic's data type.
2. Fill in the fields with the desired data values.
3. The publication module runs a python script. To validate the reception of data in the MCU. Make some of the values change in each iteration:
   ![][image21]
4. Click the gear icon (see image) to configure publishing
   ![][image22]
5. In the Code Execution Options, check the “Execute code periodically” option.
   ![][image23]
6. Run the code by clicking the Play icon. Admin Console will start publishing samples using the configured period.
   ![][image24]

## 3.3 Validate reception of data in the MCU

1. If the device has an output, and you have access to it. Confirm that the string printed after receiving correct samples is printed. **If the string is outputted, validation is OK**
2. If you don’t have access to an output, use a debugger to watch the content of the sample variable. Since Admin Console is publishing different values each time, **if you see the values changing, validation is OK.**

# Annex {#annex}

## Configuring Admin Console QoS

The previous guide explains how to validate an example application using a simple DDS-XML.  To use a production DDS-XML, you may need to configure some QoS in Admin console. This is because some datatypes may make discovery packets too large for being received in some of the MCUs.

Along with this guide, you will find an XML configuration file called *Ac qos.xml* (shipped at the same level as this document). This file contains the configuration needed to avoid the mentioned problem with MCUs using custom DDS-XML. Follow these instructions to use it in Admin Console.

1. Go to View \> Preferences.
   ![][image3]

2. In the Preferences dialog, select the Administration tab.
3. In the bottom part of the window, click on "Add File(s)...". Select the provided *Ac qos.xml* file.
   ![][image25]
4. Select “mcuLibrary::mcuCompatibleProfile” as the profile to use when joining a domain.
   ![][image26]
5. A warning will appear, this is expected, close it.
   ![][image27]
6. Click on “Apply to currently joined domains”
   ![][image28]
7. When joining new domains, make sure the profile is shown next to the domain ID:
   ![][image29]

[image1]: ../../docs/images/admin-console/image1.png
[image2]: ../../docs/images/admin-console/image2.png
[image3]: ../../docs/images/admin-console/image3.png
[image4]: ../../docs/images/admin-console/image4.png
[image5]: ../../docs/images/admin-console/image5.png
[image6]: ../../docs/images/admin-console/image6.png
[image7]: ../../docs/images/admin-console/image7.png
[image8]: ../../docs/images/admin-console/image8.png
[image9]: ../../docs/images/admin-console/image9.png
[image10]: ../../docs/images/admin-console/image10.png
[image11]: ../../docs/images/admin-console/image11.png
[image12]: ../../docs/images/admin-console/image12.png
[image13]: ../../docs/images/admin-console/image13.png
[image14]: ../../docs/images/admin-console/image14.png
[image15]: ../../docs/images/admin-console/image15.png
[image16]: ../../docs/images/admin-console/image16.png
[image17]: ../../docs/images/admin-console/image17.png
[image18]: ../../docs/images/admin-console/image18.png
[image19]: ../../docs/images/admin-console/image19.png
[image20]: ../../docs/images/admin-console/image20.png
[image21]: ../../docs/images/admin-console/image21.png
[image22]: ../../docs/images/admin-console/image22.png
[image23]: ../../docs/images/admin-console/image23.png
[image24]: ../../docs/images/admin-console/image24.png
[image25]: ../../docs/images/admin-console/image25.png
[image26]: ../../docs/images/admin-console/image26.png
[image27]: ../../docs/images/admin-console/image27.png
[image28]: ../../docs/images/admin-console/image28.png
[image29]: ../../docs/images/admin-console/image29.png
