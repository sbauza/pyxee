=====
Usage
=====

To use pyxee in a project::

    import pyxee

Authentication
--------------

The current Xee API (v3) only supports OAuth2 with Authorization code grant
like it is described in `RFC6749 section 4.1`_

For being authenticated, we need two calls to the Xee API:
 * the first one for asking a authorization code
 * the second one for passing the authorization code and getting auth tokens.

As the current way to get authorization codes is to have what we call a Web
Application flow, that means the first call to the Xee API will actually
open a new tab for your default browser asking your Xee credentials.
Since the code will be returned by Xee within a redirection URL, the current
pyxee module supports a WSGI server running a specific port.

So, that said, if you want to use pyxee for you, please do this :

1. Create a new Xee application here https://dev.xee.com/
2. Provide a redirect URI like http://localhost:<port> where port can be 8080
   by default
3. Remember the client ID and the client secret

Now all those 3 prerequisite steps are done, you can use pyxee.
For the moment, the authentication is not really automatic, but you can do
this way :

  import pyxee.client as client
  myxee = client.PyXee(client_id=<your_client_id>, client_secret=<your_secret>)
  myxee.auth()

You can also look at the pyxee.auth module and see how to use it differently.


.. _RFC6749 section 4.1: https://tools.ietf.org/html/rfc6749#section-4.1
