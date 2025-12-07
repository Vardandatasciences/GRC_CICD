import { createStore } from 'vuex'
import incidents from './modules/incidents'
import framework from './modules/framework'

const store = createStore({
  modules: {
    incidents,
    framework
  },
  strict: process.env.NODE_ENV !== 'production'
})

export default store

