var zxcvbn = require('./zxcvbn.js');
var readline = require('readline');
var rl = readline.createInterface({
  input: process.stdin,
  output: new require('stream').Writable()
});

rl.on('line', function(line){
	pwd = line;
	/* strength = zxcvbn(pwd).guesses_log10; */
	/* for use with cut down version of zxcvbn */
	strength = zxcvbn(pwd);
	process.stdout.write(strength + '\t' + pwd + '\n');
});
