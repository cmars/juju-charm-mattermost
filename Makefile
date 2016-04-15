
ifndef JUJU_REPOSITORY
	$(error JUJU_REPOSITORY is undefined)
endif

CHARM=cs:~cmars/mattermost
CHARMS=$(JUJU_REPOSITORY)/trusty/mattermost $(JUJU_REPOSITORY)/xenial/mattermost
all: $(CHARMS)

$(JUJU_REPOSITORY)/%/mattermost:
	charm build -s $*

push:
	charm push $(JUJU_REPOSITORY)/trusty/mattermost $(CHARM)

grant:
	charm grant $(CHARM) --acl read everyone

clean:
	$(RM) -r $(CHARMS)
