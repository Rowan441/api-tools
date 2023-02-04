#!/usr/bin/env python3

"""This script uses planning_domains_api to download each of the domain.pddl 
        files of the domains in the planning.domains database. Then it checks the
        stated requirements in the .pddl file and dumps that info to results.json
        If any 2 domain.pddl files in a domain set have different requirements this 
        throws an error"""

import wget
import os
import json

import planning_domains_api as api

RESULTS_DIR = "domains"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

def parse_requirements(domain_file):
        with open(domain_file, 'r') as f:
            data = f.read()
            reqs_substr_start = data.find(":requirements") + len(":requirements") + 1
            reqs_substr_end = reqs_substr_start + data[reqs_substr_start:].find(")")
            reqs = data[reqs_substr_start:reqs_substr_end].split()

        return reqs

domain_ids = map(lambda x: x["domain_id"], api.find_domains(""))

domain_reqs = {}
for domain_id in domain_ids:
    # cybersec (domain 80) currently 404's
    if domain_id == 80:
        continue

    if not os.path.exists(os.path.join(RESULTS_DIR, str(domain_id))):
        os.makedirs(os.path.join(RESULTS_DIR, str(domain_id)))

    domain_urls = set()
    domain_set_reqs = None

    problems = api.get_problems(domain_id)

    for problem in problems:
        # We only need to look at each domain.pddl file once
        domain_url = problem["domain_url"]
        if domain_url in domain_urls:
            continue
        domain_urls.add(domain_url)
        
        # Check if domain.pddl is already downloaded, otherwise download it
        domain_file_name = problem['domain_url'].split('/')[-1]
        path_to_domain_file = os.path.join(RESULTS_DIR, str(domain_id), domain_file_name)
        if os.path.isfile(path_to_domain_file):
            domain_file = path_to_domain_file
        else:
            domain_file = wget.download(domain_url, out=path_to_domain_file)

        # Verify that each domain.pddl files in a domain set have the same requirements
        reqs = parse_requirements(domain_file)
        if domain_set_reqs == None:
            domain_set_reqs = reqs
        else:
            assert(domain_set_reqs == reqs)

    # Keep track of each domain set's requirements
    domain_reqs[domain_id] = domain_set_reqs

# Write each domain set's requirements to a json file
with open(os.path.join(RESULTS_DIR, 'result.json'), 'w') as fp:
    json.dump(domain_reqs, fp, indent=2)
