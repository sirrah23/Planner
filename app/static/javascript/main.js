const getPlannerLinkWindow = () => {
    return window.location.href.split(/\//).pop()
}

const plannerApiConn = {
    get(link, cb){
        axios.get("/api/planner/"+link)
        .then(function(response){
             if(cb){
                 cb(response.data);
            }
        });
    },
    update(link, data){
        axios.post("/api/planner/"+link, {data});
    }
}

const initGroupItem = (item) => {
    const group_item = {};
    group_item.name = item.name;
    group_item.checked = item.checked;
    group_item.moved_to = "";
    return group_item;
}

const initGroupItems = (groups) => {
    const initialized_groups = {};
    for (let g in groups){
        initialized_groups[g] = groups[g].map( (i) => { return initGroupItem(i); } );
    }
    return initialized_groups;
}

const cleanGroupItem = (item) =>{
    ({name, checked} = item);
    return {name, checked};
}

const cleanGroupItems = (groups) => {
   const cleaned_groups = {}
    for (let g in groups){
        cleaned_groups[g] = groups[g].map( (i) => { return cleanGroupItem(i); } );
    }
    return cleaned_groups;
}

const app = new Vue({
   el: "#planner",
   data: {
      item: "",
      items : [],
      group: "",
      groups: {}
   },
   created: function(){
       const me = this;
       //TODO: Inject the api conn...
       plannerApiConn.get(
               getPlannerLinkWindow(),
               (respData) => {
                   me.items = respData.items;
                   me.groups = initGroupItems(respData.groups);
               });
   },
   methods: {
      add_new_item : function(event){
          if(this.item.length == 0)
              return;
          this.items.push(this.item);
          this.item = "";
          plannerApiConn.update(getPlannerLinkWindow(), JSON.stringify({items: this.items}));
      },
      add_new_group: function(event){
          if(this.group.length == 0)
              return;
          //FIXME: Group passed in that already exists...
          this.groups[this.group] = []
          this.group = "";
          // TODO: Async - cleanGroupItems could take a long time...
          // and it's very repetitive...need to find a way to not 
          // do this simple operation over and over again...
          plannerApiConn.update(getPlannerLinkWindow(), JSON.stringify({groups: cleanGroupItems(this.groups)}));
      },
      shuffle_items: function(event){
          /*
          / TODO: The algorithm should not always
          / start at the first group because if the
          / user repeatedly adds on item and shuffles
          / then the first user will get that object every
          / time.
         */
          const all_groups = Object.keys(this.groups);
          const num_groups = all_groups.length
          if(num_groups == 0)
              return;
          let curr_item, rand_idx, curr_group_idx = 0;
          while(this.items.length > 0){
              rand_idx = Math.floor(Math.random() * this.items.length);
              //TODO: Create a function to generate this object
              curr_item = {name: this.items.splice(rand_idx, 1)[0], checked: false, moved_to:""};
              this.groups[all_groups[curr_group_idx]].push(curr_item);
              curr_group_idx = (curr_group_idx + 1) % num_groups
          }
      },
      move_item: function(group_name){
          let item_to_move;
          let i;

          //Find the item that we are supposed to try and move
          for(i = 0; i < this.groups[group_name].length; i++){
              //FIXME: Hack until proper data communicator object is created...
              //Can't just do app.groups=... and app.items=... directly in the
              //create method; have to initialize with proper fields
              if(!["", undefined].includes(this.groups[group_name][i].moved_to)){
                  item_to_move = this.groups[group_name][i]
                  break;
              }
          }

          if(item_to_move === undefined)
              return;

          //If the item was somehow moved to a the group it is 
          //already in somehow then quit.
          if(item_to_move.moved_to === group_name)
              return;

          const new_group = item_to_move.moved_to;
          item_to_move.moved_to = "";

          //Finally do the actual item move 
          this.groups[new_group].push(item_to_move)
          const remove_idx = this.groups[group_name].indexOf(item_to_move);
          this.groups[group_name].splice(remove_idx,1);
          this.$forceUpdate();
      },
  },
});
