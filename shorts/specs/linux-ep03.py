SHORT = {
    'series': 'linux',
    'tag': 'EP 3',
    'hook': {'text': 'Learn ANY Linux command *without Google*', 'sub': 'man, --help, type and history',
             'who': ['mitthu', 'ollie']},
    'beats': [
        {'who': 'mitthu', 'cmd': 'whatis ls', 'out': ['ls (1)', '- list directory contents'], 'hl': 'list directory contents',
         'say': '*whatis* gives you a one-line summary of any command.'},
        {'who': 'ollie', 'big': 'man ls', 'sub': '/word = search · q = quit', 'arms': 'point',
         'say': '*man* opens the full manual. Slash searches, q quits.'},
        {'who': 'mitthu', 'cmd': 'man -k rotate', 'out': ['logrotate (8)', '- rotates, compresses,', '  and mails system logs'],
         'hl': 'logrotate (8)', 'voice': True,
         'say': 'Forgot the name? *man -k* searches every manual by keyword.'},
        {'who': 'ollie', 'cmd': 'type cd', 'out': ['cd is a shell builtin'], 'hl': 'shell builtin',
         'say': '*type* tells you if it is a builtin, an alias or a file.'},
        {'who': 'mitthu', 'cmd': 'sudo !!', 'out': ['sudo apt update', 'Hit:1 http://archive...'], 'hl': 'sudo apt update',
         'say': 'Forgot sudo? *sudo !!* reruns your last command.'},
        {'who': 'kaalu', 'cmd': 'man cd', 'error': True, 'mood': 'happy', 'arms': 'point',
         'out': ['No manual entry for cd'],
         'say': 'Ha! Builtins have *no man page*.', 'badge': 'Use: help cd'},
    ],
    'cta': {'who': ['mitthu', 'ollie', 'kaalu'],
            'lines': ['Linux Zero to Hero, Ep 3', 'New episodes Tue, Thu & Sat, 5 PM IST']},
    'cover_at': 1.6,
    'upload': {
        'title': 'Learn Any Linux Command Without Google #shorts #linux',
        'description': (
            'whatis, man, man -k, type and sudo !!: how to learn any Linux command offline, '
            'plus why man cd fails (use help cd).\n\n'
            'Full episode: "man, --help, type and which Explained with Real Examples | Linux Zero to Hero Ep 3" on the Tech-dev channel.\n'
            'New Linux episodes Tue, Thu & Sat at 5 PM IST.\n\n'
            '#shorts #Linux #DevOps #SRE #LinuxCommands #TechDev'),
        'tags': ['linux', 'linux commands', 'man command', 'linux help', 'type command', 'sudo !!', 'shorts',
                 'linux for beginners', 'bash', 'devops', 'sre', 'linux zero to hero', 'tech-dev'],
    },
}
