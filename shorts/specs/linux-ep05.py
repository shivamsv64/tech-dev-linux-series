SKIT = {
    'series': 'linux',
    'tag': 'EP 5',
    'banner': 'When mv silently overwrites your config',
    'scenes': [
        {'shot': 'wide', 'set': 'desk_night',
         'cast': [{'who': 'rohan', 'mood': 'calm', 'pose': 'type'}],
         'say': 'Linux *mv* will overwrite a file without asking. Silently.'},
        {'shot': 'screen', 'cmd': 'mv new.conf app.conf',
         'say': 'Rohan moves the new config over the old one. No warning.'},
        {'shot': 'eye', 'who': 'rohan', 'mood': 'calm',
         'say': 'No error, no message. Everything looks *fine*.'},
        {'shot': 'wide', 'set': 'desk_night',
         'cast': [{'who': 'khanna', 'mood': 'angry', 'pose': 'point', 'x': 790},
                  {'who': 'rohan', 'mood': 'worried', 'pose': 'headhold', 'x': 380}],
         'laptop_x': 380,
         'say': 'Then Khanna asks where the old production settings went.'},
        {'shot': 'face', 'who': 'rohan', 'mood': 'panic', 'fx': ['lines', 'sweat'],
         'say': 'They were in the file he just *replaced*.'},
        {'shot': 'wide', 'set': 'desk_night',
         'cast': [{'who': 'rohan', 'mood': 'tired', 'pose': 'headhold', 'x': 380},
                  {'who': 'meera', 'mood': 'smug', 'pose': 'mug', 'stand': True, 'x': 790}],
         'laptop_x': 380, 'mug': False,
         'say': 'Meera shows him the flag he should have used.'},
        {'shot': 'screen', 'cmd': 'mv -i new.conf app.conf', 'out': ["mv: overwrite 'app.conf'?"],
         'hl': 'overwrite', 'say': 'With *mv -i*, Linux asks before it overwrites.'},
        {'shot': 'screen', 'cmd': 'mv -b new.conf app.conf', 'badge': '-b = keep a backup',
         'say': 'And *mv -b* keeps the old file as a backup.'},
        {'shot': 'wide', 'set': 'desk_night',
         'cast': [{'who': 'rohan', 'mood': 'happy', 'pose': 'cheer', 'fx': ['sparkle']}],
         'say': 'Rohan makes the safe flag his *habit*.'},
        {'shot': 'card', 'set': 'plain', 'big': 'mv -i', 'sub': 'ask first. or -n to never overwrite',
         'say': 'Save this. Add *-i* before you move.'},
    ],
    'cta': {'set': 'office'},
    'cover_at': 1.2,
    'upload': {
        'title': 'When mv Silently Overwrites Your Config #shorts #linux',
        'description': (
            'mv overwrites the destination file without asking. Use mv -i to be prompted, or mv -n to never '
            'overwrite.\n\n'
            'Full episode: "Copy, move, rename and wildcards" on the Tech-dev channel.\n\n'
            '#shorts #Linux #DevOps #SRE #LinuxCommands #TechDev'),
        'tags': ['linux', 'mv command', 'mv -i', 'mv -n', 'linux commands', 'linux for beginners', 'shorts',
                 'bash', 'devops', 'linux zero to hero', 'tech-dev'],
    },
}

# Shivam's Chatterbox clone only
SKIT['voice'] = 'chatterbox-shivam'
