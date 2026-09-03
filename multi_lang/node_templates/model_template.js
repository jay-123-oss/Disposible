// Template: Mongoose model (raw). Placeholders substituted by NodeModelGenerator.
const mongoose = require('mongoose');

const __MODEL_NAME__Schema = new mongoose.Schema({
  name: { type: String, required: true },
  price: { type: Number, required: true }
});

module.exports = mongoose.model('__MODEL_NAME__', __MODEL_NAME__Schema);