Development
-----------

Preconditions: install `uv <https://github.com/astral-sh/uv>`_.

Run tests with `uvx tox -e test`.

To run the add-on in Plone 6.1:
- create a requirements.txt file with the following content:
  ::
    -c https://dist.plone.org/release/6.1-latest/constraints.txt
    Plone
    -e .

- create a venv and install the requirements and activate it:
  ::
    uv venv
    uv pip install -r requirements.txt
    source .venv/bin/activate

- create a ``instance.yaml`` file with the following content:
  ::
      default_context:
          initial_user_password: admin
          debug_mode: true
          zcml_package_includes: pas.plugins.headers, Products.CMFPlone

- generate configuration: ``uvx cookiecutter --no-input -f --config-file instance.yaml gh:plone/cookiecutter-zope-instance``
- start Zope/Plone with plugin: ``runwsgi instance/etc/zope.ini``
- In your browser go to http://localhost:8080/
- Create a "Classic" site
- Go to admin -> site setup -> Add-ons and install pas.plugins.headers
- at http://localhost:8080/Plone/acl_users/request_headers/manage_propertiesForm edit the properties

Proceed as described in the README.rst.