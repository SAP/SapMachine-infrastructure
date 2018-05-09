# Update Mirror OpenJDK Branches

This jenkins pipeline is used to setup an update the github brachnes, that mirror OpenJDK mercurial repositories.

The bash script `update_repos.sh` accepts an OpenJDK repo name as argument.
To transform and update the mercurial repository `hg.openjdk.java.net:/jdk/jdk` the script is started as follows:

```
update_repo.sh jdk/jdk
```

The script depends onn the mercurial extension `hg-git` and the git extension `git-hg-again`. Both extensions are installed in the Dockerfile in this directory.

As working directory the current directory is used. The mercurial repository is cloned using `git hg clone` into a directory corresponding to the name of the repo. This command transforms the mrecurial repository into a git repository. This operation might take several hours.
The transformed repository is pushed as a new branch to github. 

In case the script finds a directory with a corresponding name, it is assumed, that this repo is already transformed and it is just updated using `git hg pull`. This operation will usually take a few seconds.




