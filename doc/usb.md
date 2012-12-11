Current MakerBot machines use an ATmega8U2 for USB communication.
The ATmega8U2 is programmed with a custom VID/PID pair that identifies the type of machine.

Some Thing-o-Matics and many other popular brands of 3D printers are based on the Arduino Mega.
The Arduino Mega also uses an ATmega8U2 (or a close relative like a ATmega32U2) with a custom VID/PID pair.

Older MakerBot machines use a generic USB serial cable based on an FTDI chip.

<table>
    <thead>
        <tr>
            <th>VID</th>
            <th>PID</th>
            <th>Device</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>0403</td>
            <td>6001</td>
            <td>FTDI FT232BM/L/Q, FT245BM/L/Q, FT232RL/Q, FT245RL/Q</td>
        </tr>
        <tr>
            <td>0403</td>
            <td>6010</td>
            <td>FTDI FT2232C/D/L, FT2232HL/Q</td>
        </tr>
        <tr>
            <td>0403</td>
            <td>6011</td>
            <td>FTDI FT4232HL/Q</td>
        </tr>
        <tr>
            <td>0403</td>
            <td>6014</td>
            <td>FTDI FT232HL/Q</td>
        </tr>
        <tr>
            <td>2341</td>
            <td>0010</td>
            <td>Arduino Mega</td>
        </tr>
        <tr>
            <td>23C1</td>
            <td>D314</td>
            <td>Replicator</td>
        </tr>
        <tr>
            <td>23C1</td>
            <td>B015</td>
            <td>Replicator 2</td>
        </tr>
    </tbody>
</table>

Information on FTDI VID and PID combinations is from

> Technical Note TN_100
>
> USB Vendor ID / Product ID # Guidelines
>
> [http://www.ftdichip.com/Support/Documents/TechnicalNotes/TN_100_USB_VID-PID_Guidelines.pdf](http://www.ftdichip.com/Support/Documents/TechnicalNotes/TN_100_USB_VID-PID_Guidelines.pdf)
