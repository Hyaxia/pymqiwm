# pymqiwm
A wrapper module for pymqi

When i statred to use the pymqi module, i had no idea how to do certain things.
As time went, to perform the things I needed, I had to find code examples only to try and somehow hit the target as to
what is the proper syntax.

There are few objects that we can interact with as a developer when talking about the websphere queue manager.
I have created a wrapper to the pymqi package that lets you easily interact with the queue manager and any of its queues.
You are more than welcome to check any of the methods that are used so that you will get a basic understanding of how the
pymqi module works.

I hope that this piece of code will be helpful for anyone who tries to use the pymqi module.


Few pieces of the code where used from the project https://github.com/dsuch/pymqi/blob/master/docs/examples.rst, full credit goes to him.
I encourage you to check his work.

pymqiwm : What You Need From Pymqi
==========================

pymqiwm is focused on making interaction of the user with the IBM MQ 
infrastructure easier.

![image](easy.jpg)

How easy is it your ask? here's an answer:

``` {.sourceCode .python}
>>> with queue:
>>>     for message in queue.browse_messages():
>>>         print(message)
will print all the messages in the queue
>>>     queue.put("test message")
>>>     queue.get()
b"test message"
>>>     
>>> with qmgr:
>>>     qmgr.create_local_queue(name="LOCAL")
```

Pymqi lets you hide all the complicated interface wit the pymqi package
behind easy to understand and easy to use functions.

Feature Support
---------------

-   Easy to understand interface
-   Making business logic much more clearer
-   Never leaving open handlers (`with` context managers)
-   Enables to put and get messages from queue whenever you want 
(which is not the case with pymqi, gotta handle different `open` options)
Requests officially supports Python 2.7 & 3.4–3.7, and runs great on
PyPy.

How to Contribute
-----------------

1.  Fork [the repository](https://github.com/Hyaxia/pymqiwm) on
    GitHub to start making your changes to the **master** branch (or
    branch off of it).
2.  Send a pull request.

Pymqi
-----

This repository is using the [pymqi](https://github.com/dsuch/pymqi) package, recommend you check it out.


