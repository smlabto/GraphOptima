# Email Notification System Setup Tutorial

> Note: if you want to setup a email notification but the code is raising error because it is missing a `key` file, you will need to change the config to disable email notification under the `optimizer` field



In this tutorial, we'll guide you through setting up the email notification system in the External API Monitor module using iCloud. Please note that while this tutorial focuses on iCloud, users are free to choose their own email service provider.

## Step-by-step instructions

### 1. Generate an App-Specific Password from iCloud

Generate an app-specific password from iCloud by following [Apple's official guide](https://support.apple.com/en-us/HT204397).

### 2. Create and Save Key File

After generating the password, save it into a `key` file. You can do this by opening your terminal and running the following command:
```bash
nano key
```

Please note that this file has been excluded from the GitHub repository due to security reasons.


### 3. Enter App-Specific Password

Paste your app-specific password in the `key` file, save and close this file. Make sure that the `key` file is saved under the same folder as the `external_api.py`.

### 4. Change the sending and receiving addresses

In the config file `config.json`, change the `email_from` and `email_to` fields.


### 5. Run the External API Monitor node

You can now run the External API Monitor node, which will use the `key` file to enable the email notification service. As the Optimizer calls the External API Monitor node, the email service will send email notifications to the designated email address.


### 6. Customize the content of email notification

To use the email notification feature in the framework, import `external_api` and use the `write_instruction` function to create an `email_instruction` file with a subject line and message.

```python
external_api.write_instruction(subject="Optimization finished!",
                                   message="A multi objective NSGA2 optimization has been finished on Cedar.",

                                   instruction_type="email_instruction")
```

`write_instruction` will create a temp file that ends with `email_instruction`. This file is stored under the same folder as the `external_api.py`, which will be scanned and opened by the External Api Monitor node, and subsequently removed after the email has been sent. 
