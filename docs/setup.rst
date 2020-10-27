Installing it
=============

First of all you have to install this package to use it. To do this, follow one of the following methods:

From (test)pypi
---------------

To install the latest stable version of this package, run the following command. (Assuming you have Python already installed)

.. code-block::

   python -m pip install --upgrade lemon_markets

To install the latest (development) version of this package, just add one parameter.

.. code-block::

   python -m pip install --upgrade --index-url https://test.pypi.org/simple/ lemon_markets

Directly from the GitHub repository
-----------------------------------

Also using pip, you can change the url, to download the github repo to get the latest possible version of this package.

.. code-block::

   python -m pip install --upgrade git+https://github.com/leonhma/lemon_markets.git#egg=lemon_markets

Getting your personal access-token
==================================

* If you haven't already, sign up for an account over at `lemon.markets <https://app.lemon.markets/registration>`_

* Now, you can create a new strategy in your dashboard. Choose a name, click next, and also choose a description.

* When you'll be asked for the name of your acess-token, choose a memorable name, in case you later have to delete it.

* **Important:** Give your acess-token full permissions, so that we don't have any issues along the way of this tutorial.

* Congrats! You have just created your first Strategy. Now write down your token, open your favourite python editor and :doc:`get started <get_started>`!
