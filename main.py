from pyinfra import host
from pyinfra.operations import apt, files, init, server, ssh

# Define the hosts
nodes = [host('node{}'.format(i)) for i in range(1, 11)]

# Install WireGuard on all nodes
apt.packages(
    name='Install WireGuard',
    packages=['wireguard-tools'],
    update=True,
    host=nodes,
)

# Generate WireGuard keys
ssh.keygen(
    name='Generate WireGuard keys',
    key_filename='wireguard-key',
    bits=4096,
    force=True,
    host=nodes,
)

# Create WireGuard configuration file for each node
for i, node in enumerate(nodes):
    peers = [n for n in nodes if n != node]

    config_lines = [
        '[Interface]',
        'PrivateKey = <private_key>',
        'Address = 10.0.0.{}/32'.format(i + 1),
        'ListenPort = 51820',
    ]

    for peer in peers:
        config_lines.append('[Peer]')
        config_lines.append('PublicKey = <public_key_of_peer>')
        config_lines.append('AllowedIPs = 10.0.0.{}/32'.format(nodes.index(peer) + 1))
        config_lines.append('Endpoint = {}:51820'.format(peer.fact.ipv4_address))

    wireguard_config = '\n'.join(config_lines)

    files.put(
        name='Create WireGuard config',
        src=files.temp_file(wireguard_config),
        dest='/etc/wireguard/wg0.conf',
        host=node,
    )

# Enable and start WireGuard on all nodes
init.systemd(
    name='Enable WireGuard service',
    service='wg-quick@wg0',
    running=True,
    enabled=True,
    host=nodes,
)

# Restart WireGuard to apply the new configuration
server.shell(
    name='Restart WireGuard',
    commands=['systemctl restart wg-quick@wg0'],
    host=nodes,
)
