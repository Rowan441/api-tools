#!/usr/bin/env python3

"""This script uses planning_domains_api to download each of the domain.pddl 
        files of the domains in the planning.domains database. Then it checks the
        stated requirements in the .pddl file and dumps that info to results.json
        If any 2 domain.pddl files in a domain set have different requirements this 
        throws an error"""

import wget
import os, subprocess
import json, re

import planning_domains_api as api

RESULTS_DIR = "domains"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

def parse_requirements(domain_file):
        with open(domain_file, 'r+') as f, \
             open(domain_file+".noreqs") as f2:
            domain = f.readlines()
            f.seek(0)
            for line in domain:
                if ":requirements" not in line:
                    f2.write(line)
            f2.truncate()

            # req_index = domain.find(":requirements")
            # reqs_substr_start = domain.rfind('(', 0, req_index)
            # reqs_substr_end = domain.find(")", req_index)

            # # remove requirements from domain
            # domain = domain[:reqs_substr_start] + domain[reqs_substr_end+1:]

        val_output = str(subprocess.check_output(["./Parser", domain_file+".noreqs"]))
        reqs = map(lambda x: x[1], re.findall("(?<=(Undeclared requirement ))(:[a-zA-Z-]+)", val_output))

        return list(set(reqs))

domain_ids = map(lambda x: x["domain_id"], api.find_domains(""))

domain_reqs = {}
for domain_id in domain_ids:
    # cybersec (domain 80) currently 404's
    if domain_id == 80:
        continue

    if domain_id != 8:
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

        # Parse file for states requirements
        with open(domain_file, 'r') as f:
            domain = f.read()
            req_index = domain.find(":requirements")
            reqs_substr_start = req_index + 14 #domain.rfind('(', 0, req_index)
            reqs_substr_end = domain.find(")", req_index)

        # remove requirements from domain
        reqs_stated = domain[reqs_substr_start:reqs_substr_end].split()
        print(reqs_substr_start, reqs_substr_end)
        print(reqs_stated)

        # Verify that each domain.pddl files in a domain set have the same requirements
        reqs = parse_requirements(domain_file)
        if domain_set_reqs == None:
            domain_set_reqs = reqs
            domain_stated_set_reqs = reqs_stated
        else:
            assert(domain_set_reqs == reqs)
            assert(domain_stated_set_reqs == reqs_stated)

    # Keep track of each domain set's requirements
    domain_reqs[domain_id] = {}
    domain_reqs[domain_id]["stated"] = domain_stated_set_reqs
    domain_reqs[domain_id]["val"] = domain_set_reqs


# Write each domain set's requirements to a json file
with open(os.path.join(RESULTS_DIR, 'result.json'), 'w') as fp:
    json.dump(domain_reqs, fp, indent=2)