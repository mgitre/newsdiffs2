var keys = Object.keys(articledata);
var tags = {"headline":"h1", "subhead":"h4", "body":null};

tagArray = ["<p>","<h1>","<h2>","<h3>","<h4>","<h5>","<h6>","</p>","</h1>","</h2>","</h3>","</h4>","</h5>","</h6>"];
tagsForDiffs = ["<del>","</del>","<ins>","</ins>"]
diffCost = 12;

function nonComparisonView(n){
    var content = "";
    var version = articledata[keys[n]];
    if(!!version["headline"]){
        content += '<h1 class="headline">'+version["headline"]+'</h1>';
    }
    if(!!version["subhead"]){
        content += '<h4 class="subhead">'+version["subhead"]+'</h4>';
    }
    content += version["body"];
    document.getElementById("article").innerHTML = content;
}

function compareNthArticles(n, n2){
    var ns = [n,n2];
    var dmp = new diff_match_patch();
    dmp.Diff_ShowPara = false;
    document.getElementById("article").innerHTML = "";
    for(var j = 0; j < 3; j++){
        element = ["headline","subhead","body"][j]
        var content = ["",""];
        for(var i = 0; i < 2; i++){
            var version = articledata[keys[ns[i]]];
            content[i] = version[element];
            if(!!content[i]){
                for(var x = 0; x < tagArray.length; x++){
                    content[i] = content[i].replace(new RegExp(tagArray[x],'g'), String.fromCharCode(2048+x));
                }
            }
            else{
            content[i] = "";
            }
        }
        var diff = dmp.diff_main(content[0],content[1]);
        dmp.Diff_EditCost = diffCost;
        dmp.diff_cleanupEfficiency(diff);
        var nicelyformatted = "";
        for(var i = 0; i < diff.length; i++){
            for(var x = 0; x < tagArray.length; x++){
                diff[i][1] = diff[i][1].replace(new RegExp(String.fromCharCode(2048+x),'g'), tagArray[x]);
            }
            var difftype = diff[i][0];
            var splitup = diff[i][1].split(/(<[^>]*?>)/g);
            for(var x = 0; x < splitup.length; x++) {
                var entry = splitup[x];
                if(entry.length == 0) { continue; }
                if(!/<[^>]*>/.test(entry) && difftype != 0) {
                    nicelyformatted += tagsForDiffs[difftype+1]+entry+tagsForDiffs[difftype+2];
                } else {
                    nicelyformatted += entry;
                }
            }
        }
        var tag = tags[element];
        if(!!tag){
        document.getElementById("article").innerHTML+="<"+tags[element]+">"+nicelyformatted+"</"+tags[element]+">";
        }
        else{
        document.getElementById("article").innerHTML+=nicelyformatted;
        }
    }
}

function buttonPressed(){
    var checked = document.querySelectorAll('[name="checkbox"]:checked');
    if (checked.length==1){
        nonComparisonView(checked[0].id);
    }
    else if (checked.length==2){
        compareNthArticles(checked[0].id, checked[1].id);
    }
    else{
        alert("Please select either one or two checkboxes");
    }
}

function checkboxChecked(box){
    if(box.checked){
        box.parentElement.style.backgroundColor = 'red';
        if(currentlyChecked==2){
            var altbox = document.getElementById(checkboxToReplace);
            altbox.checked = false;
            checkboxToReplace = parseInt(document.querySelector('[name="checkbox"]:not([id="'+box.id+'"]):checked').id);
            altbox.parentElement.style.backgroundColor='aqua';
        } else {
            currentlyChecked = 2;
        }
    }
    else {
        if(currentlyChecked==2){
            box.parentElement.style.backgroundColor = 'aqua';
            currentlyChecked = 1;
            checkboxToReplace = parseInt(document.querySelector('[name="checkbox"]:checked').id);
        } else{
        box.checked=true;
        }
    }
}

checkboxToReplace = keys.length-2;
currentlyChecked = 2;
if (keys.length==1){
    currentlyChecked=1;
}
for(var i = 0; i < keys.length; i++){
    //document.getElementById("articleinfo").innerHTML += '<b>'+keys[i]+': </b><br><a href="#" onclick="compareNthArticles('+i+')">Compare to previous version</a> <a href="#" onclick="nonComparisonView('+i+')">View only this version</a><br>';
    div = document.createElement("div");
    div.className = "checkboxdiv";
    checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "checkbox";
    checkbox.onclick = function() {checkboxChecked(this);};
    checkbox.id = i;
    label = document.createElement("label");
    label.for = i;
    label.innerHTML = keys[i];
    div.appendChild(checkbox);
    div.appendChild(label);
    if ([keys.length-1, keys.length-2].includes(i)){ checkbox.checked = true; div.style.backgroundColor = 'red';}
    document.getElementById("articleinfo").appendChild(div);

    //document.getElementById("articleinfo").appendChild(document.createElement("br"));
}

output = document.createElement("output");
output.id = "output";
output.innerHTML = diffCost;
slider = document.createElement("input");
slider.type = "range";
slider.id = "slider";
slider.min = 1;
slider.max = 20;
slider.value = diffCost;
document.getElementById("articleinfo").appendChild(slider);
document.getElementById("articleinfo").appendChild(output);
document.getElementById("slider").oninput = function() {
    diffCost = document.getElementById("slider").value;
    document.getElementById('output').innerHTML=diffCost;
};
button = document.createElement("button");
button.onclick = function(){buttonPressed();}
button.innerHTML = "Refresh";
document.getElementById("articleinfo").appendChild(button);
compareNthArticles(keys.length-2, keys.length-1);
