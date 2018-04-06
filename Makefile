define HELP

 The Trac Makefile is here to help automate development and
 maintenance tasks.

 Please use `make <target>' where <target> is one of:

  package             create the plugin's package
  clean               delete all compiled files
  status              show which Python is used and other infos

  [python=...]        variable for selecting Python version
  [pythonopts=...]    variable containing extra options for the interpreter


 ---------------- L10N tasks

  init-xy             create catalogs for given xy locale

  extraction          regenerate the catalog templates

  update              update all the catalog files from the templates
  update-xy           update the catalogs for the xy locale only

  compile             compile all the catalog files
  compile-xy          compile the catalogs for the xy locale only

  check               verify all the catalog files
  check-xy            verify the catalogs for the xy locale only

  stats               detailed translation statistics for all catalogs
  stats-pot           total messages in the catalog templates
  stats-xy            translated, fuzzy, untranslated for the xy locale only

  summary             display percent translated for all catalogs
  summary-xy          display percent translated for the xy locale only
                      (suitable for a commit message)

  diff                show relevant changes after an update for all catalogs
  diff-xy             show relevant changes after an update for the xy locale
  [vc=...]            variable containing the version control command to use

  [locale=...]        variable for selecting a set of locales

  [updateopts=...]    variable containing extra options for update (e.g. -N)


 ---------------- Code checking tasks

  pylint              check code with pylint
  jinja               check Jinja2 templates
  coffee              compile .coffee script files into .js files

  [module=...]        module or package to check with pylint
  [templates=...]     list of Jinja2 templates to check
  [coffeescripts=...] list of coffee script files to compile


 ---------------- Testing tasks

  unit-test           run unit tests
  functional-test     run functional tests
  test-wiki           shortcut for running all wiki unit tests
  test                run all tests
  coverage            run all tests, under coverage

  [db=...]            variable for selecting database backend
  [test=...]          variable for selecting a single test file
  [testopts=...]      variable containing extra options for running tests
  [coverageopts=...]  variable containing extra options for coverage

endef
# `
export HELP

# ----------------------------------------------------------------------------
#
# Main targets
#
# ----------------------------------------------------------------------------

.PHONY: all package help status clean clean-bytecode clean-mo

%.py : status
	$(PYTHON) setup.py -q test -s $(subst /,.,$(@:.py=)).test_suite $(testopts)

ifdef test
all: status
	$(PYTHON) setup.py -q test -s $(subst /,.,$(test:.py=)).test_suite $(testopts)
else
all: help
endif

package:
	$(PYTHON) setup.py bdist_egg

help:
	@echo "$$HELP"

help_variables = $(filter HELP_%,$(.VARIABLES))
help_targets = $(filter-out help-CFG,$(help_variables:HELP_%=help-%))

status:
	@echo
	@echo "Python: $$(which $(PYTHON)) $(pythonopts)"
	@echo
	@echo "Variables:"
	@echo "  PATH=$$PATH"
	@echo "  PYTHONPATH=$$PYTHONPATH"
	@echo "  TRAC_TEST_DB_URI=$$TRAC_TEST_DB_URI"
	@echo "  server-options=$(server-options)"
	@echo
	@echo "External dependencies:"
	@printf "  Git version: "
	@git --version 2>/dev/null || echo "not installed"
	@printf "  Subversion version: "
	@svn --version -q 2>/dev/null || echo "not installed"
	@echo

Trac.egg-info: status
	$(PYTHON) setup.py egg_info

clean: clean-bytecode clean-mo clean-build-files

clean-bytecode:
	find . -name \*.py[co] -print -delete

clean-build-files:
	@echo "Deleting temporary files that created in building package[s] ..."
	@rm -frv ./*.egg-info ./build ./dist

Makefile: ;


# ----------------------------------------------------------------------------
#
# L10N related tasks
#
# ----------------------------------------------------------------------------

catalogs = messages messages-js

ifdef locale
    locales = $(locale)
else
    locales = $(wildcard /locale/*/LC_MESSAGES/messages.po)
    locales := $(subst ticket_template/locale/,,$(locales))
    locales := $(subst /LC_MESSAGES/messages.po,,$(locales))
    locales := $(sort $(locales))
endif

# Note: variables only valid within a $(foreach catalog,...) evaluation
catalog.po = ticket_template/locale/$(*)/LC_MESSAGES/$(catalog).po
catalog.pot = ticket_template/locale/$(catalog).pot
catalog_stripped = $(subst messages,,$(subst -,,$(catalog)))
_catalog = $(if $(catalog_stripped),_)$(catalog_stripped)

.PHONY: extract extraction update compile check stats summary diff


init-%:
	@$(foreach catalog,$(catalogs), \
	    [ -e $(catalog.po) ] \
	    && echo "$(catalog.po) already exists" \
	    || $(PYTHON) setup.py init_catalog$(_catalog) -l $(*);)


extract extraction:
	$(PYTHON) setup.py $(foreach catalog,$(catalogs),\
	    extract_messages$(_catalog))


update-%:
	$(PYTHON) setup.py $(foreach catalog,$(catalogs), \
	    update_catalog$(_catalog) -l $(*)) $(updateopts)

ifdef locale
update: $(addprefix update-,$(locale))
else
update:
	$(PYTHON) setup.py $(foreach catalog,$(catalogs), \
	    update_catalog$(_catalog)) $(updateopts)
endif


compile-%:
	$(PYTHON) setup.py $(foreach catalog,$(catalogs), \
	    compile_catalog$(_catalog) -l $(*)) \
	    generate_messages_js -l $(*)

ifdef locale
compile: $(addprefix compile-,$(locale))
else
compile:
	$(PYTHON) setup.py $(foreach catalog,$(catalogs), \
	    compile_catalog$(_catalog)) generate_messages_js
endif


check: pre-check $(addprefix check-,$(locales))
	@echo "All catalogs checked are OK"

pre-check:
	@echo "checking catalogs for $(locales)..."

check-%:
	@printf "$(@): "
	$(PYTHON) setup.py $(foreach catalog,$(catalogs), \
	    check_catalog$(_catalog) -l $(*))
	@$(foreach catalog,$(catalogs), \
	    msgfmt --check $(catalog.po) &&) echo msgfmt OK
	@rm -f messages.mo


stats: pre-stats $(addprefix stats-,$(locales))

pre-stats: stats-pot
	@echo "translation statistics for $(locales)..."

stats-pot:
	@echo "translation statistics for catalog templates:"
	@$(foreach catalog,$(catalogs), \
	    printf "$(catalog.pot): "; \
	    msgfmt --statistics $(catalog.pot);)
	@rm -f messages.mo

stats-%:
	@$(foreach catalog,$(catalogs), \
	    [ -e $(catalog.po) ] \
	    && { printf "$(catalog.po): "; \
	         msgfmt --statistics $(catalog.po); } \
	    || echo "$(catalog.po) doesn't exist (make init-$(*))";)
	@rm -f messages.mo


summary: $(addprefix summary-,$(locales))

define untranslated-sh
LC_ALL=C msgfmt --statistics $(catalog.pot) 2>&1 \
  | tail -1 \
  | sed -e 's/0 translated messages, \([0-9]*\) un.*/\1/'
endef

define translated-sh
{ LC_ALL=C msgfmt --statistics $(catalog.po) 2>&1 || echo 0; } \
    | tail -1 \
    | sed -e 's/[^0-9]*\([0-9]*\) translated.*/\1/'
endef

MESSAGES_TOTAL = \
    $(eval MESSAGES_TOTAL := ($(foreach catalog,$(catalogs), \
                                  $(shell $(untranslated-sh)) + ) 0)) \
    $(MESSAGES_TOTAL)

summary-%:
	@$(PYTHON) -c "print('l10n/$(*): translations updated (%d%%)' \
	    % (($(foreach catalog,$(catalogs), \
	          $(shell $(translated-sh)) + ) 0) * 100.0 \
	       / $(MESSAGES_TOTAL)))"
	@rm -f messages.mo


diff: $(addprefix diff-,$(locales))

vc ?= svn

diff-%:
	@diff=l10n-$(*).diff; \
	$(vc) diff ticket_template/locale/$(*) > $$diff; \
	[ -s $$diff ] && { \
	    printf "# $(*) changed -> "; \
	    $(PYTHON) contrib/l10n_diff_index.py $$diff; \
	} || rm $$diff

# The above creates l10n-xy.diff files but also a l10n-xy.diff.index
# file pointing to "interesting" diffs (message changes or addition
# for valid msgid).
#
# See also contrib/l10n_sanitize_diffs.py, which removes in-file
# *conflicts* for line change only.

clean-mo:
	find ticket_template/locale -name \*.mo -print -delete
	find ticket_template/htdocs/locale -name \*.js -print -delete


# ----------------------------------------------------------------------------
#
# Code checking tasks
#
# ----------------------------------------------------------------------------

.PHONY: pylint jinja coffee

pylintopts = --persistent=n --init-import=y \
--disable=E0102,E0211,E0213,E0602,E0611,E1002,E1101,E1102,E1103 \
--disable=F0401 \
--disable=W0102,W0141,W0142,W0201,W0212,W0221,W0223,W0231,W0232, \
--disable=W0401,W0511,W0603,W0613,W0614,W0621,W0622,W0703 \
--disable=C0103,C0111 \

ifdef module
pylint:
	pylint $(pylintopts) $(subst /,.,$(module:.py=))
else
pylint:
	pylint $(pylintopts) trac tracopt
endif


templates ?= $(shell \
    find $$(find trac tracopt -type d -a -name templates) \
        -mindepth 1 -maxdepth 1 -type f | \
    grep -v "~" | grep -v README )

jinja:
	$(PYTHON) contrib/jinjachecker.py $(jinjaopts) $(templates)

coffeescripts ?= $(shell find trac tracopt -name \*.coffee)



# ----------------------------------------------------------------------------
#
# Testing related tasks
#
# ----------------------------------------------------------------------------

.PHONY: test unit-test functional-test test-wiki

test: unit-test functional-test

unit-test: Trac.egg-info
	$(PYTHON) ./ticket_template/test.py --skip-functional-tests $(testopts)

functional-test: Trac.egg-info
	$(PYTHON) ticket_template/tests/functional/__init__.py $(testopts)

test-wiki:
	$(PYTHON) ticket_template/tests/allwiki.py $(testopts)



# ----------------------------------------------------------------------------
#
# Coverage related tasks
#
# (see http://nedbatchelder.com/code/coverage/)
#
# ----------------------------------------------------------------------------

COVERAGEOPTS ?= --branch --source=trac,tracopt

.PHONY: coverage clean-coverage show-coverage

coverage: clean-coverage test-coverage show-coverage

clean-coverage:
	coverage erase
	@rm -fr htmlcov

ifdef test
test-coverage:
	coverage run $(test) $(testopts)
else
test-coverage: unit-test-coverage functional-test-coverage
endif

unit-test-coverage:
	coverage run -a $(coverageopts) $(COVERAGEOPTS) \
	    ticket_template/test.py --skip-functional-tests $(testopts)

functional-test-coverage:
	FIGLEAF='coverage run -a $(coverageopts) $(COVERAGEOPTS)' \
	$(PYTHON) ticket_template/tests/functional/__init__.py -v $(testopts)

show-coverage: htmlcov/index.html
	$(if $(START),$(START) $(<))

htmlcov/index.html:
	coverage html --omit=*/__init__.py



# ============================================================================
#
# Setup environment variables

PYTHON ?= python
PYTHON := $(PYTHON) $(pythonopts)

python-home := $(python.$(or $(python),$($(db).python)))

ifeq "$(findstring ;,$(PATH))" ";"
    SEP = ;
    START ?= start
else
    SEP = :
    START ?= xdg-open
endif

ifeq "$(OS)" "Windows_NT"
    ifndef python-home
        # Detect location of current python
        python-exe := $(shell python -c 'import sys; print(sys.executable)')
        python-home := $(subst \python.exe,,$(python-exe))
        ifeq "$(SEP)" ":"
            python-home := /$(subst :,,$(subst \,/,$(python-home)))
        endif
    endif
    python-bin = $(python-home)$(SEP)$(python-home)/Scripts
endif

define prepend-path
$(if $2,$(if $1,$1$(SEP)$2,$2),$1)
endef

PATH-extension = $(call prepend-path,$(python-bin),$(path.$(python)))
PYTHONPATH-extension = $(call prepend-path,.,$(pythonpath.$(python)))

export PATH := $(call prepend-path,$(PATH-extension),$(PATH))
export PYTHONPATH := $(call prepend-path,$(PYTHONPATH-extension),$(PYTHONPATH))
export TRAC_TEST_DB_URI = $($(db).uri)

# Misc.
space = $(empty) $(empty)
comma = ,
