The AI's Instructions for GPing tool in this project

**Gping is for Windows environments using tcping.exe that is located in the root directory
GPing is a tool used in grocery stores to monitor network connectivity. It is a simple and effective tool that can be used to diagnose network issues and improve network performance.**

GPing will use a CSV for logging that is in the root directory and should always be in the root directory for data to send to the ISP or NCR for troubleshooting
    This file should be named GPing12052024.csv where 12052024 is the current date
    This file should have the following headers:
        Timestamp, Event Type, IP Address, Status, Response Time (ms), Network Type, Details, Total Pings, Failed Pings, Packet Loss %
    This file should be updated with new events as they happen
    This file should never get overwritten
    This file should be saved in the root directory
    This file should report the following events:
        "Timestamp,Event Type,IP Address,Status,Response Time (ms),Network Type,Details,Total Pings,Failed Pings,Packet Loss %"
       

GPing will test the gateway address and it automatically detect the IP address of the gateway
Gping will test the Google DNS address and it will be a fixed entry

Gping Gui
    This gui will show the current status of the gateway and Google DNS
    This gui will show connected/starting/disconnected for both the gateway and Google DNS
    This gui has a Connection log for easy viewing for the technician
    This gui has a Start button to start the tests
    This gui has a Stop button to stop the tests
    This gui needs to have check to have options to turn the test on or off for EACH IP in the GUI

Gping Gui will have a network profile section that will show the current network type
    This gui will have a check button that will show the current network type