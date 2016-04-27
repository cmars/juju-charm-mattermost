
ifndef JUJU_REPOSITORY
	$(error JUJU_REPOSITORY is undefined)
endif

CHARM=cs:~cmars/mattermost
CHARMS=$(JUJU_REPOSITORY)/trusty/mattermost $(JUJU_REPOSITORY)/xenial/mattermost
BDIST_VERSION=2.2.0

all: $(CHARMS)

$(JUJU_REPOSITORY)/%/mattermost: bdist/mattermost.tar.gz
	charm build -s $*

bdist/mattermost.tar.gz:
	-mkdir -p $(shell dirname $@)
	wget -O $@ https://releases.mattermost.com/$(BDIST_VERSION)/mattermost-team-$(BDIST_VERSION)-linux-amd64.tar.gz

push: $(JUJU_REPOSITORY)/trusty/mattermost bdist/mattermost.tar.gz
	charm push $(JUJU_REPOSITORY)/trusty/mattermost $(CHARM) --resource bdist=bdist/mattermost.tar.gz

grant:
	charm grant $(CHARM) --acl read everyone

clean:
	$(RM) -r $(CHARMS)
