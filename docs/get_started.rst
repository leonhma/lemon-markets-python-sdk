Getting started
===============

After creating your account and access-token in the :doc:`setup <setup>`, you can now open your favourite python editor and get started using this module right away.
Just copy and paste the code below:

.. code-block:: python

   import lemon_markets # importing it

   from time import sleep # import sleep

   lemon_markets.__debug_flag__ = True # enable debugging so that you can see what happens


   # demonstrating websockets

   def callback(instrument, price, time): # define the callback to call when websocket data is received