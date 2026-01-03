profile_name = "Desktop Environment"

packages = [
    "vim",
    "git",
    "networkmanager",
    "xorg",
    "plasma",
    "konsole"
]

post_install_commands = [
    "systemctl enable NetworkManager",
    "echo 'Welcome to your new Arch Desktop!' > /etc/motd"
]
