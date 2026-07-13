const path = require('path');
const heroic = require(path.join(__dirname, '..', 'lib', 'heroic-core'));

console.log('Lade heroic-core...');
console.log('Version:', heroic.version);
console.log('Info:', heroic.info());
console.log('Init:', heroic.init());
