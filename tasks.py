# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License.

import importlib.metadata
import json
import os
import webbrowser

import requests
from invoke import task
from monty.os import cd

"""
Deployment file to facilitate releases.
"""

__author__ = "Shyue Ping Ong, Anubhav Jain"
__email__ = "ongsp@ucsd.edu"
__date__ = "Sep 1, 2014"
fw_version = f"v{importlib.metadata.version('fireworks')}"


@task
def make_doc(ctx):
    with cd("docs_rst"):
        ctx.run("sphinx-apidoc -o . -f ../fireworks")
        ctx.run("make html")

    with cd("docs"):
        ctx.run("cp -r html/* .")
        ctx.run("rm -r html")
        ctx.run("rm -r doctrees")

        # Avoid the use of jekyll so that _dir works as intended.
        ctx.run("touch .nojekyll")


@task
def update_doc(ctx):
    make_doc(ctx)
    with cd("docs"):
        ctx.run("git add .")
        ctx.run(f'git commit -a -m "Update to {fw_version}"')
        ctx.run("git push")


@task
def publish(ctx):
    ctx.run("python setup.py release")


@task
def release_github(ctx):
    payload = {
        "tag_name": fw_version,
        "target_commitish": "master",
        "name": fw_version,
        "body": "",
        "draft": False,
        "prerelease": False,
    }
    # For this to work properly, you need to go to your Github profile, generate
    # a "Personal access token". Then do export GITHUB_RELEASES_TOKEN="xyz1234"
    # (or add it to your bash_profile).
    response = requests.post(
        "https://api.github.com/repos/materialsproject/fireworks/releases",
        data=json.dumps(payload),
        headers={"Authorization": "token " + os.environ["GITHUB_RELEASES_TOKEN"]},
    )
    print(response.text)


@task
def release(ctx, nosetest=False):
    if nosetest:
        ctx.run("nosetests")
    publish(ctx)
    update_doc(ctx)
    release_github(ctx)


@task
def open_doc(ctx):
    pth = os.path.abspath("docs/index.html")
    webbrowser.open("file://" + pth)
