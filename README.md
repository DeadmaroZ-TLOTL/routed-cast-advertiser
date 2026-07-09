# Routed Cast Advertiser

Home Assistant custom integration that advertises routed Google Cast devices on the local LAN.

It is useful when a Cast speaker is reachable by IP, but its mDNS discovery packets are trapped behind another routed subnet.

## What it does

Routed Cast Advertiser publishes a synthetic `_googlecast._tcp.local` mDNS record from Home Assistant.
This lets clients on the Home Assistant LAN discover a Cast device that is actually behind another routed network, as long as the Cast TCP ports are reachable through routing, NAT, or a local proxy address.

It does not proxy Cast traffic by itself. Your router or firewall still needs to make the Cast device reachable on the advertised IP address and port.

## Installation

Copy `custom_components/cast_mdns_advertiser` into your Home Assistant `custom_components` directory and restart Home Assistant.

The integration can then be configured from:

`Settings > Devices & services > Add integration > Routed Cast Advertiser`

## Configuration

Add one advertised Cast device from the UI.

Required fields:

- `Name`: Friendly display name, for example `Trailer speaker`.
- `Local proxy IP address`: The IP address visible from the Home Assistant LAN.
- `Cast port`: Usually `8009`.
- `Cast UUID`: The UUID from the real Cast device.

Optional fields:

- `Model`: Cast model name, for example `Google Nest Mini`.
- `mDNS instance name`: Override the generated service instance.
- `mDNS host name`: Override the generated mDNS target host.
- `Cast boot/session value`: Optional `bs` TXT value from the real device.

## Router Requirements

The advertised IP address should accept TCP connections for the Cast ports you want to use, normally:

- `8008`
- `8009`
- `8443`

For example, a router can advertise a LAN-side proxy IP and forward those ports to the real Cast speaker on another subnet.

## Notes

This integration is meant for routed home networks where normal mDNS forwarding is not available or is not enough for Google Cast discovery.
