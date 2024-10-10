# Chronos: AI Dungeon Master assistant

Summary: We are building an AI assistant which acts like a Dungeon master for a simplified version of the game Dungeons and Dragon. 

### Requirements:

- Narrate the scenario
- Keeps scores of players.  
- Add obstacles 
- Add chaos
- Interpret rules

### Stretch goals
- Generate visuals depending on scenario. 
- Multiple players
- Audio output to read out the scenario. 

## Configuration

1. **API Keys**: 
   - Copy the `.env.sample` file and rename it to `.env`
   - Replace the placeholder values with your actual API keys and Runpod endpoints
   - Note: Runpod keys are optional

2. **Model Selection**:
   - Choose the desired model by setting the `config_key` variable in `app.py`.

3. **System Prompts and Class Context**:
   - Adjust the `ENABLE_SYSTEM_PROMPT` and `ENABLE_CLASS_CONTEXT` flags as needed.

4. **Customize Prompts**:
   - Modify the prompt templates in the `prompts.py` file to suit your educational context.

## Running the Application

1. **Activate the Virtual Environment** (if not already activated):
   ```sh
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
2. **Install dependencies**

Install the project dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

- Copy the `.env.sample` file to a new file named `.env`
- Fill in the `.env` file with your API keys


4. **Run the Chainlit App**:
   ```sh
   chainlit run app.py -w
   ```
   Open your browser and navigate to the URL displayed in the terminal.
   
## Running Evaluation
1. **Generate the Evaluation Dataset**
   ```sh
   python generate_dataset.sh
   ```
2. **Verify in Langfuse:** Check that the dataset 'chronos-qa-pairs' is created.
3. **Run the Evaluation**
   ```sh
   python evaluate_rag.py
   ```
4. **Verify in Langfuse:** Check the traces 'chronos-qa' has run.

## Tasks

- [x] Add tracing
- [ ] Add judgement
- [ ] 