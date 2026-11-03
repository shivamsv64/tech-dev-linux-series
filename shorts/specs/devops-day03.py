SHORT = {
    'series': 'devops',
    'tag': 'DAY 3',
    'hook': {'text': 'Same bug: *5 minutes* or a lost weekend?', 'sub': 'DevOps & SRE Zero to Hero, Day 3',
             'who': ['ollie', 'kaalu']},
    'beats': [
        {'who': 'ollie', 'big': 'SDLC', 'sub': 'plan · define · design · build · test · deploy',
         'say': 'Every app goes through *six phases*: the SDLC.', 'extra': 0.9},
        {'who': 'ollie', 'big': 'DEVOPS = LOOP', 'sub': 'same phases, run many times a day', 'arms': 'point',
         'say': 'DevOps runs the same phases as a *fast loop*.', 'extra': 0.9},
        {'who': 'mitthu', 'say': 'Requirement says 1000 *or more*. Test it!',
         'cmd': 'python3 -m unittest',
         'out': ['AssertionError: 1000 != 900', 'FAILED (failures=1)'],
         'hl': ['1000 != 900', 'FAILED'], 'extra': 0.5, 'voice': True},
        {'who': 'mitthu', 'say': 'Fix greater-than to *greater or equal*.',
         'cmd': 'python3 -m unittest',
         'out': ['Ran 2 tests in 0.000s', 'OK'],
         'hl': 'OK', 'extra': 0.8},
        {'who': 'kaalu', 'say': 'Deploy first, test later? *Customers find it!*',
         'cmd': 'bash deploy_late.sh',
         'out': ['Deployed v1.0', 'FAILED (failures=1)'],
         'error': True, 'badge': 'Test first!', 'mood': 'sly', 'extra': 0.6},
        {'who': 'bablu', 'big': 'SHIFT LEFT', 'sub': 'tests + scans inside the build', 'arms': 'up', 'mood': 'happy',
         'say': 'Find bugs *early*: a bug in production costs way more.', 'extra': 0.8},
    ],
    'cta': {'who': ['ollie', 'mitthu', 'bablu', 'kaalu'],
            'lines': ['DevOps & SRE Zero to Hero, Day 3', 'New lesson every day, 8 PM IST']},
    'upload': {
        'title': 'SDLC in 6 steps: where DevOps fits #shorts #devops',
        'description': (
            'Every app goes through 6 SDLC phases: plan, define, design, build, test, deploy. '
            'DevOps runs them as a fast loop and shifts tests left, so a bug costs 5 minutes, not a weekend.\n\n'
            'Full lesson: "SDLC in 6 Steps: Where DevOps Fits | DevOps & SRE Zero to Hero Day 3" on the Tech-dev channel.\n'
            'Free 100-day course, new lesson every day at 8 PM IST.\n\n'
            '#shorts #DevOps #SDLC #SRE #TechDev'),
        'tags': ['sdlc', 'software development life cycle', 'devops', 'sdlc phases', 'shift left',
                 'devops for beginners', 'devops lifecycle', 'python unittest', 'devops zero to hero',
                 'sre', 'shorts', 'devops day 3', 'tech-dev'],
    },
}
