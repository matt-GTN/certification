# Automatic Fraud Detection 🥷

**90min**

**Solution**

---

## Context 📇

Fraud is a huge issue among financial institutions. In the EU in 2019, the **European Central Bank** estimated that fraudulent credit card transactions amounted more €1 billion! 😮

AI can really help solve this issue by detecting fraudulent payments in a very precise manner. This usecase is actually now one of the most famous one among Data Scientists.

However, eventhough we managed to build powerful algorithms, the hard thing is now to use them in production. This means predict fraudulent payment in real-time and respond appropriately.

---

## Project goals 🎯

Business has come to your team because they need to:

* Get notified once a fraud is detected. They told you that they just need a notification though
* Once every morning, they need to check all the payments and frauds that happened during the previous day

---

## Where to get data

To achieve this project, you will need to get access to some data! Here are two data sources that you can use:

* **Fraudulent Payments full dataset**
   * This dataset contains a large amount of payments labelled as fraudulent or not
   * Use this to create your algorithm!
* **Real-time payment API**
   * This API retrieves real-time payments
   * Use this to create real-time predictions
   * The API gets updated every minute

---

## Deliverables 📬

To complete this project, you will need to produce:

* A schema of the infrastructure you chose to build and whyyou built it that way
   * This can be in a Powerpoint, Word document
   * You can get inspiration from the below picture
* The source code of all elements necessary to build your infrastructure
* A video of your working infrastructure on an example
   * You can use **Vidyard** to do so

---

## Tips 🦮

To help you in your task, we would like to give you a few tips on how to tackle that project.

### How can I build the algorithm?

To build you algorithm, you can use any library (`sklearn`, `tensorflow`), **APIs** or even **No-code** tools.

If you don't want to build the algorithm yourself, feel free to use AmazonML, which is a great API tool. Check out our **online-course on the matter**

Remember to build something that is reusable! Especially in terms of preprocessing, using an algorithm is not only about using a `.predict()` 😉

**IMPORTANT**

The most important part is the Data Pipeline - NOT THE ML Algorithm

No matter what you do, the ML algorithm comes second after the Data Pipeline which should be your main priority.

### I don't know where to start

First things first, in this project you need to at least:

* Train an algorithm
* Stage it into production
* Store real-time data in a db

This is our recommandation on where to start:

**IMPORTANT**

The above example is just a suggestion, you can deviatefrom this infrastructure, and most likely there are alternatives that might be smarter, easier to implement and more efficient. The only minimal elements we need to have are:

* An element collecting & storing data
* An element consuming data
* An ETL (or ELT) process

### How do I split work among my teammates?

Working together is key here! You can split your work several ways, but here is a suggestion:

* One team member can train the algorithm
* One team member can build MLflow infrastructure
* One team member can create the real-time data ingestion pipeline