//TODO: Refactor group into key-value pairs where key is group name
const app = new Vue({
   el: "#planner",
   data: {
      item: "",
      items : [],
      group: "",
      groups: {}
   },
   methods: {
      add_new_item : function(event){
          if(this.item.length == 0)
              return;
          this.items.push(this.item);
          this.item = "";
      },
      add_new_group: function(event){
          if(this.group.length == 0)
              return;
          //FIXME: Group passed in that already exists...
          this.groups[this.group] = []
          this.group = "";
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
              curr_item = {"name": this.items.splice(rand_idx, 1)[0], "checked": false, moved_to:""};
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
