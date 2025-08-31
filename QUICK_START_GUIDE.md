# AURA Quick Start Guide

## 🚀 Get AURA Running in 5 Minutes

### Step 1: Install LM Studio

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Install and open the application

### Step 2: Load a Model

1. In LM Studio, click **"Discover"** tab
2. Search for and download one of these models:
   - **For full functionality**: `microsoft/Phi-3.5-vision-instruct` (vision + text)
   - **For fast text**: `microsoft/Phi-3-mini-4k-instruct` (text only)
   - **For best vision**: `xtuner/llava-phi-3-mini` (vision + text)
3. Click **"My Models"** tab
4. Click **"Load"** next to your downloaded model
5. Wait for it to fully load (status shows "Loaded")

### Step 3: Start the API Server

1. Click **"Local Server"** tab in LM Studio
2. Click **"Start Server"**
3. Verify it shows "Server running on port 1234"

### Step 4: Test LM Studio Setup

```bash
python check_lmstudio.py
```

You should see all green checkmarks ✅

### Step 5: Test AURA's Dynamic Detection

```bash
python test_dynamic_model.py
```

This should show your loaded model is detected.

### Step 6: Run AURA

```bash
python main.py
```

## 🎯 What Model Should I Use?

### For Beginners (Recommended)

- **Phi-3.5 Vision Instruct** (3.8B) - Small, fast, supports vision
- **Moondream2** (1.8B) - Tiny, very fast, good vision

### For Best Performance

- **LLaVA v1.6 Mistral 7B** - Excellent vision, good reasoning
- **LLaVA v1.6 Vicuna 7B** - Alternative with different personality

### For Speed (Text Only)

- **Phi-3 Mini** (3.8B) - Very fast, good reasoning
- **Gemma 2 2B** (2B) - Extremely fast, basic reasoning

## 🔧 Common Issues

### "Cannot connect to LM Studio"

- Make sure LM Studio is open
- Check that the server is started (Local Server tab)
- Verify port 1234 is not blocked

### "No model detected"

- Load a model in LM Studio (My Models tab)
- Wait for it to fully load before testing
- Try restarting the LM Studio server

### "Tests pass but AURA won't start"

- Check API keys are set (see main README)
- Verify microphone permissions
- Run `python setup_check.py` for full diagnosis

## 🎉 Success!

Once everything is working:

- Say **"Computer"** to wake AURA
- Try: **"Computer, what's on my screen?"**
- Or: **"Computer, click the search button"**

## 📚 Next Steps

- Read the full [README.md](README.md) for advanced features
- Check [DYNAMIC_MODEL_IMPLEMENTATION_SUMMARY.md](DYNAMIC_MODEL_IMPLEMENTATION_SUMMARY.md) for technical details
- Explore different models to find your preferred balance of speed vs capability
