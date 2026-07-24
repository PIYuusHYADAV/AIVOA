import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  messages: [
    {
      role: 'assistant',
      content:
        "Upload a complaint document or paste the customer's message below — I'll extract the details and fill the form for you.",
    },
  ],
  progress: 0,       // 0-100, drives the extraction progress bar
  isExtracting: false,
  isThinking: false, // chat round-trip in progress (no progress bar, just typing dots)
  pastedText: '',
}

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    messageSent(state, action) {
      state.messages.push({ role: 'user', content: action.payload })
    },
    messageReceived(state, action) {
      state.messages.push({ role: 'assistant', content: action.payload })
    },
    extractionStarted(state) {
      state.isExtracting = true
      state.progress = 8
    },
    extractionProgress(state, action) {
      state.progress = action.payload
    },
    extractionFinished(state) {
      state.isExtracting = false
      state.progress = 100
    },
    thinkingStarted(state) {
      state.isThinking = true
    },
    thinkingFinished(state) {
      state.isThinking = false
    },
    pastedTextChanged(state, action) {
      state.pastedText = action.payload
    },
    chatReset(state) {
      state.messages = [initialState.messages[0]]
      state.progress = 0
      state.isExtracting = false
      state.isThinking = false
      state.pastedText = ''
    },
  },
})

export const {
  messageSent,
  messageReceived,
  extractionStarted,
  extractionProgress,
  extractionFinished,
  thinkingStarted,
  thinkingFinished,
  pastedTextChanged,
  chatReset,
} = chatSlice.actions

export default chatSlice.reducer
