SHORT = {
    'series': 'linux',
    'tag': 'EP 1',
    'hook': {'text': '5 Linux commands every *beginner* needs', 'sub': 'Linux Zero to Hero, Ep 1 in 30 seconds',
             'who': ['mitthu', 'ollie']},
    'beats': [
        {'who': 'mitthu', 'cmd': 'whoami', 'out': ['shivam'], 'hl': 'shivam',
         'say': '*whoami* tells you which user you are logged in as.'},
        {'who': 'mitthu', 'cmd': 'hostname', 'out': ['tech-dev'], 'hl': 'tech-dev',
         'say': '*hostname* shows the name of this machine.'},
        {'who': 'ollie', 'cmd': 'uname -r', 'out': ['6.8.0-47-generic'], 'hl': '6.8.0-47-generic',
         'say': '*uname -r* prints the kernel version. Super handy on servers.'},
        {'who': 'ollie', 'cmd': 'echo $SHELL', 'out': ['/bin/bash'], 'hl': '/bin/bash',
         'say': '*echo $SHELL* shows which shell you are using.'},
        {'who': 'mitthu', 'cmd': 'grep PRETTY /etc/os-release', 'out': ['PRETTY_NAME="Ubuntu 24.04.1 LTS"'],
         'hl': 'Ubuntu', 'say': 'Which Linux is this? */etc/os-release* knows.'},
        {'who': 'kaalu', 'cmd': 'Whoami', 'error': True, 'mood': 'happy', 'arms': 'point',
         'out': ["Command 'Whoami' not found,", "did you mean: command", "'whoami' from deb coreutils"],
         'say': 'Ha! Capital W breaks it. Linux is *case-sensitive*.', 'badge': 'Use lowercase!'},
    ],
    'cta': {'who': ['mitthu', 'ollie', 'kaalu'],
            'lines': ['Linux Zero to Hero, Ep 1', 'New episode every day, 5 PM IST']},
    'cover_at': 1.6,
    'upload': {
        'title': '5 Linux Commands Every Beginner Needs #shorts #linux',
        'description': (
            'whoami, hostname, uname -r, echo $SHELL and /etc/os-release: the first 5 commands to run on any '
            'new Linux server, plus the case-sensitive mistake every beginner makes.\n\n'
            'Full episode: "Linux for Beginners: Your First 5 Commands | Linux Zero to Hero Ep 1" on the Tech-dev channel.\n'
            'New Linux episode every day at 5 PM IST.\n\n'
            '#shorts #Linux #DevOps #SRE #LinuxCommands #TechDev'),
        'tags': ['linux', 'linux commands', 'linux for beginners', 'shorts', 'whoami', 'uname', 'linux tutorial',
                 'devops', 'sre', 'bash', 'ubuntu', 'linux zero to hero', 'tech-dev'],
    },
}
