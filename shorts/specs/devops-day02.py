SHORT = {
    'series': 'devops',
    'tag': 'DAY 2',
    'hook': {'text': 'A *10-minute* fix — 10 days to ship?', 'sub': 'DevOps & SRE Zero to Hero, Day 2',
             'who': ['tortoise', 'cheetah']},
    'beats': [
        {'who': 'tortoise', 'big': '10 DAYS', 'sub': 'code review → testing → change board', 'mood': 'tired', 'arms': 'down',
         'say': 'Review. Test. Approval. Deploy. *Every. Single. Time.*', 'extra': 0.5},
        {'who': 'cheetah', 'big': '< 1 HOUR', 'sub': 'same fix, with a pipeline', 'mood': 'happy', 'arms': 'up',
         'say': 'Pipeline. Push. *Done.* Every hand-off is a queue.', 'extra': 0.5},
        {'who': 'ollie', 'big': 'set -e', 'sub': 'stop on any failure',
         'say': 'The deploy script needs *set minus e*: if a test fails, it stops.', 'extra': 0.5},
        {'who': 'mitthu', 'say': 'Watch: *bash deploy.sh*',
         'cmd': 'bash deploy.sh',
         'out': ['1/3 Running tests...', '2/3 Building app...', '+3/3 Deploying...'],
         'hl': '3/3 Deploying', 'extra': 0.5},
        {'who': 'kaalu', 'say': 'No set minus e? It *deploys anyway!*',
         'cmd': 'bash deploy_bad.sh',
         'out': ['!Tests failed, rc=1', '2/3 Building app...', '+3/3 Deploying...'],
         'error': True, 'badge': 'Add set -e!', 'mood': 'sly'},
    ],
    'cta': {'who': ['cheetah', 'tortoise', 'ollie', 'mitthu'],
            'lines': ['DevOps & SRE Zero to Hero, Day 2', 'New lesson every day, 8 PM IST']},
    'upload': {
        'title': '10-day fix vs 1-hour fix: why DevOps? #shorts #devops',
        'description': (
            'A 10-minute fix took 10 days to reach users — not because of slow developers, '
            'but because of waiting between teams. Every hand-off is a queue. '
            'A pipeline plus set -e ships the same fix in under an hour.\n\n'
            'Full lesson: "Why a 10-Minute Fix Took 10 Days | DevOps & SRE Zero to Hero Day 2" on the Tech-dev channel.\n'
            'Free 100-day course, new lesson every day at 8 PM IST.\n\n'
            '#shorts #DevOps #SRE #CICD #TechDev'),
        'tags': ['devops', 'why devops', 'devops explained', 'devops for beginners', 'ci cd pipeline',
                 'set -e bash', 'deploy script', 'devops zero to hero', 'sre', 'shorts',
                 'devops day 2', 'release process', 'tech-dev'],
    },
}
