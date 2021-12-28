.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Account Xunnel
==============

This app allows you to synchronize your bank statements from Xunnel with Odoo and add new accounts.


**How To**
----------

Set Up Your Instance
--------------------

- If you don't have any Xunnel Account you must create one at www.xunnel.com.

- Log in to your account.

- Sync the accounts or banks that you need in the company.

- Copy the token of the company.

- Go to **Accounting > Configuration > Settings > Xunnel > Set Up Token** and paste the token in Xunnel Token field.

.. figure:: account_xunnel/static/description/set-up-token-menuitem.jpg


Download Xunnel Accounts
------------------------

- Go to **Accounting > Configuration > Xunnel > Download Accounts**.

.. figure:: account_xunnel/static/description/download-accounts-menuitem.jpg

Then press the button "ACCEPT & DOWNLOAD".

.. figure:: account_xunnel/static/description/accept-and-download-button.jpg

If the synchronization was successful you could check those accounts in **Accounting > Configuration > Accounting > Online Synchronization**


Link An Account to A Journal
----------------------------

- To create a new Journal go to **Accounting > Configuration > Accounting > Journals**.

- Click the **Create** button and make sure that your journal has *Type* as **Bank** and *Bank Feeds* as **Automated Bank Synchronization**.

.. figure:: account_xunnel/static/description/journal-config.jpg

- Go to **Accounting > Configuration > Accounting > Online Synchronization** and select the account you want, in the form view click the **Edit** button and select the journal you just created to the **Journals** field of any account.

.. figure:: account_xunnel/static/description/account-link-to-journal-config.jpg

- Go to **Accounting > Dashboard** and inside your journal kanban click the link **Synchronize now**.

.. figure:: account_xunnel/static/description/sync-now-link.jpg

Those movements could be seen by clicking on the title of your journal.


Add A New Account
-----------------

To create a new Account go to **Accounting > Configuration > Xunnel > Credential Creator**.

.. figure:: account_xunnel/static/description/credential-creator-menuitem.jpg

.. figure:: account_xunnel/static/description/add-new-account.jpg

- Follow the steps of the widget to add your new account.

- When you finished repeat the process of *Download Accounts* to see your brand new account.


To check more videos go to https://xunnel.com/en_US/user-manual

**Maintainer**
--------------

.. image:: https://xunnel.com/logo.png
   :alt: Xunnel
   :target: https://www.xunnel.com/

This module is maintained by Xunnel.
