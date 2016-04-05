# Juju reactive charm layer for Mattermost

From the [Mattermost](http://www.mattermost.org) website:

As an alternative to proprietary SaaS messaging, Mattermost brings all your
team communication into one place, making it searchable and accessible
anywhere.

Mattermost is:

* Slack-compatible, not Slack-limited – Mattermost features rival Slack features, and support a superset of Slack’s incoming and outgoing webhook integrations, including compatibility with existing Slack integrations. From your existing Slack teams, you can import users, public channel history and even theme setting colors into Mattermost. Mattermost mobile experience with comment threads and file sharing
* Accessible on web, desktop, phone and tablet – Use Mattermost from your iOS or Android phones and tablets or with installed apps on Windows, Linux and Mac. Easy to deploy, manage, upgrade and extend– Mattermost is written in Golang and React and runs as a single Linux binary with either MySQL or Postgres. Every month on the 16th a new compiled version is released under an MIT license.
* Supported by a vibrant community – Use Mattermost with dozens of community integrations and applications, including Jira, IRC, XMPP, Hubot, Giphy, Jenkins, GitLab, Trac, Redmine, SVN, RSS/Atom and many others. Build and share your own apps using Mattermost APIs and drivers.

# Building

In this directory:

    $ charm build

# Deploying

To deploy the locally-built charm:

    $ juju deploy local:trusty/mattermost
    $ juju deploy postgresql
    $ juju add-relation postgresql:db mattermost:db

# TODO

- Randomly generate encryption keys and salts during install hook.
- `website` relation to support reverse-proxying.

# Contact

Casey Marshall <charmed at cmars.tech>

