- Make sure the yaml db is mounted in the prod env and updated with the new objects when the user updates the db - also need to decide how to sync the prod db with the local db.

- Massive UI changes are needed - we would like to have a easier way to edit / add items and table view for the objects.

- Currently the yaml is not eferencing any id for the objects neither the orignal file they came from.
    - This is a problem because we need to be able to trace the source file and page that the object was created from and return them to the user
    
    - Solution is quite simple - we need to add a new field to the yaml file that will be the id of the object and the original file and page that the object was created from. The actuall details will be inserted manullay.


-- Tommorow --


- The llm call is slow and we are just loading the entire file into the llm - we would like to have a 'search' tool available to the llm, that will allow the llm to search the file for the relevant information.

-Currently there is no evaluation set of questions and answers - we would like to have a set of questions and answers that we can use to evaluate the llm's performance and run it through the llm to see if it can answer the questions correctly.

- We also would like to have a OCR tool availabe to the user in order to upload new obejct and items to the db.

- Whatsapp integration - we would like to have a whatsapp integration that will allow the user to send a message to the bot and get a response.