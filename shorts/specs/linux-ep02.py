SHORT = {
    'series': 'linux',
    'tag': 'EP 2',
    'hook': {'text': 'Never get *lost* in Linux again', 'sub': 'pwd, cd and ls in 40 seconds',
             'who': ['mitthu', 'ollie']},
    'beats': [
        {'who': 'mitthu', 'cmd': 'pwd', 'out': ['/home/shivam'], 'hl': '/home/shivam',
         'say': '*pwd* tells you exactly which folder you are in.'},
        {'who': 'mitthu', 'cmd': 'cd projects; pwd', 'out': ['/home/shivam/projects'], 'hl': 'projects',
         'say': '*cd* moves you into a folder. Here: projects.'},
        {'who': 'ollie', 'big': 'cd ..', 'sub': 'one folder up · cd - = go back', 'arms': 'point',
         'say': 'Two dots mean the *parent* folder. cd dash jumps back.'},
        {'who': 'ollie', 'big': '/var/log', 'sub': 'starts with / = absolute path', 'voice': True,
         'say': 'Start with a slash and the path works *from anywhere*.'},
        {'who': 'mitthu', 'cmd': 'ls -t ~/releases', 'out': ['app-v42.tar.gz', 'app-v41.tar.gz', 'app-v40.tar.gz'],
         'hl': 'app-v42.tar.gz', 'say': '*ls -t* lists by time. Newest release on top!'},
        {'who': 'kaalu', 'cmd': 'cd client docs', 'error': True, 'mood': 'happy', 'arms': 'point',
         'out': ['bash: cd: too many arguments'],
         'say': 'Ha! A *space* splits the name in two.', 'badge': 'cd "client docs"'},
    ],
    'cta': {'who': ['mitthu', 'ollie', 'kaalu'],
            'lines': ['Linux Zero to Hero, Ep 2', 'New episode every day, 5 PM IST']},
    'cover_at': 1.6,
    'upload': {
        'title': 'Never Get Lost in Linux Again: pwd, cd, ls #shorts #linux',
        'description': (
            'pwd shows where you are, cd moves you, ls shows what is there. Plus absolute vs relative paths, '
            'cd .., cd - and the folder-with-a-space mistake every beginner makes.\n\n'
            'Full episode: "pwd, cd and ls Explained with Real Examples | Linux Zero to Hero Ep 2" on the Tech-dev channel.\n'
            'New Linux episode every day at 5 PM IST.\n\n'
            '#shorts #Linux #DevOps #SRE #LinuxCommands #TechDev'),
        'tags': ['linux', 'linux commands', 'cd command', 'ls command', 'pwd command', 'shorts',
                 'linux for beginners', 'linux navigation', 'devops', 'sre', 'bash', 'linux zero to hero',
                 'tech-dev'],
    },
}
