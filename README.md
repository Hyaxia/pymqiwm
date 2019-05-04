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
will iterate over all message in the queue and print them one by one
>>>     queue.put("test message")
>>>     queue.get()
b"test message"
>>>     
>>> with qmgr:
>>>     qmgr.create_local_queue(name="LOCAL")
```

pymqiwm lets you hide all the complicated interface wit the pymqi package
behind easy to understand and easy to use functions.

Feature Support
---------------

-   Easy to understand interface
-   Much clearer business logic, hiding all the low lvl interaction for the wrapper to handle
-   Safe connection handling, no open connections are left behind (`with` context managers)
-   Enables free use of the queue object, reading a writing as you will, 
(which is not the case with pymqi, there is a need to handle different `open` options)
-   Out of the box functionality that lest you browse and read messages in a sophisticated way

How to Contribute
-----------------

1.  Fork [this repository](https://github.com/Hyaxia/pymqiwm) on
    GitHub to start making your changes to the **master** branch (or
    branch off of it).
2.  Send a pull request.

Pymqi
-----

This repository is using the [pymqi](https://github.com/dsuch/pymqi) package, recommend you check it out.


